from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from resources.swagger_modules import data_manifests, data_manifests_return
from resources.utils import get_project_permissions
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from models.api_meta_class import MetaAPI
from services.logger_services.logger_factory_service import SrvLoggerFactory
from models.api_data_manifest import DataAttributeModel, DataManifestModel, TypeEnum, db
from .utils import has_permissions, is_greenroom, get_file_node_bygeid, get_trashfile_node_bygeid, \
    has_valid_attributes, check_attributes, get_folder_node_bygeid
from services.permissions_service.decorators import permissions_check
from services.permissions_service.utils import has_permission
from api import module_api
from flask import request
import re
import math
import requests
import json
import time

api_ns_data_manifests = module_api.namespace(
    'Data Manifests Restful', description='For data manifest feature', path='/v1')
api_ns_data_manifest = module_api.namespace(
    'Data Manifest Restful', description='For data manifest feature', path='/v1')

_logger = SrvLoggerFactory('api_data_manifest').get_logger()


class APIDataManifest(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_data_manifests.add_resource(
            self.RestfulManifests, '/data/manifests')
        api_ns_data_manifest.add_resource(
            self.RestfulManifest, '/data/manifest/<manifest_id>')
        api_ns_data_manifest.add_resource(
            self.RestfulAttributes, '/data/attributes')
        api_ns_data_manifest.add_resource(
            self.RestfulAttribute, '/data/attribute/<id>')
        # api_ns_data_manifest.add_resource(
        #     self.FileManifests, '/file/manifest/attach') ## deprecated
        api_ns_data_manifest.add_resource(self.FileManifest, '/file/<file_geid>/manifest')
        api_ns_data_manifest.add_resource(
            self.ValidateManifest, '/file/manifest/validate')
        api_ns_data_manifest.add_resource(
            self.ImportManifest, '/import/manifest')
        api_ns_data_manifest.add_resource(
            self.ExportManifest, '/export/manifest')
        api_ns_data_manifest.add_resource(
            self.FileManifestQuery, '/file/manifest/query')
        api_ns_data_manifest.add_resource(
            self.AttachAttributes, '/file/attributes/attach')

    class RestfulManifests(Resource):
        @api_ns_data_manifest.expect(data_manifests)
        @api_ns_data_manifest.response(200, data_manifests_return)
        @jwt_required()
        @permissions_check('file_attribute_template', '*', 'view')
        def get(self):
            """
            List manifests by project_code
            """
            try:
                response = requests.get(
                    ConfigClass.ENTITYINFO_SERVICE + "manifests", params=request.args)
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling entityinfo service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

        @jwt_required()
        @permissions_check('file_attribute_template', '*', 'create')
        def post(self):
            """
            Create a data manifest
            """
            try:
                response = requests.post(
                    ConfigClass.ENTITYINFO_SERVICE + "manifests", json=request.get_json())
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling entityinfo service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class RestfulManifest(Resource):
        # @jwt_required()
        def get(self, manifest_id):
            """
            Get a data manifest and list attributes
            """
            my_res = APIResponse()
            manifest = db.session.query(DataManifestModel).get(manifest_id)
            if not manifest:
                my_res.set_code(EAPIResponseCode.not_found)
                my_res.set_error_msg('Manifest not found')
            else:
                result = manifest.to_dict()
                # if not has_permission(result.get("project_code"), 'file_attribute_template', '*', 'view'):
                #    my_res.set_code(EAPIResponseCode.forbidden)
                #    my_res.set_error_msg('Permission Denied')
                #    return my_res.to_dict, my_res.code
            try:
                response = requests.get(
                    ConfigClass.ENTITYINFO_SERVICE + f"manifest/{manifest_id}")
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling entityinfo service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

        @jwt_required()
        def put(self, manifest_id):
            my_res = APIResponse()
            data = request.get_json()
            update_fields = ["name", "project_code"]
            manifest = db.session.query(DataManifestModel).get(manifest_id)
            if not manifest:
                my_res.set_code(EAPIResponseCode.not_found)
                my_res.set_error_msg('Manifest not found')
                return my_res.to_dict, my_res.code

            # Permissions check
            if not has_permission(manifest.project_code, 'file_attribute_template', '*', 'update'):
                my_res.set_code(EAPIResponseCode.forbidden)
                my_res.set_result("Permission Denied")
                return my_res.to_dict, my_res.code

            try:
                response = requests.put(
                    ConfigClass.ENTITYINFO_SERVICE + f"manifest/{manifest_id}", json=data)
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling entityinfo service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

        @jwt_required()
        def delete(self, manifest_id):
            """
            Delete an manifest 
            """
            my_res = APIResponse()
            manifest = db.session.query(DataManifestModel).get(manifest_id)
            if not manifest:
                my_res.set_code(EAPIResponseCode.not_found)
                my_res.set_error_msg('Manifest not found')
                return my_res.to_dict, my_res.code

            # Permissions check
            if not has_permission(manifest.project_code, 'file_attribute_template', '*', 'delete'):
                my_res.set_code(EAPIResponseCode.forbidden)
                my_res.set_result("Permission Denied")
                return my_res.to_dict, my_res.code

            try:
                response = requests.delete(
                    ConfigClass.ENTITYINFO_SERVICE + f"manifest/{manifest_id}")
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling entityinfo service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class RestfulAttributes(Resource):
        @jwt_required()
        def post(self):
            """
            Bulk Create attribute
            """
            api_response = APIResponse()
            attributes = request.get_json()
            for data in attributes:
                # Permissions check
                if not has_permission(data.get("project_code"), 'file_attribute_template', '*', 'create'):
                    api_response.set_code(EAPIResponseCode.forbidden)
                    api_response.set_result("Permission Denied")
                    return api_response.to_dict, api_response.code
            data = {
                "attributes": attributes
            }

            try:
                response = requests.post(
                    ConfigClass.ENTITYINFO_SERVICE + "attributes", json=data)
                return api_response.to_dict, api_response.code
            except Exception as e:
                _logger.error(
                    f"Error when calling entityinfo service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class RestfulAttribute(Resource):
        @jwt_required()
        def put(self, id):
            """
            Update an attribute
            """
            my_res = APIResponse()
            data = request.get_json()
            update_fields = ["name", "attribute",
                             "value", "optional", "project_code"]
            attribute = db.session.query(DataAttributeModel).get(id)
            if not attribute:
                my_res.set_code(EAPIResponseCode.not_found)
                my_res.set_error_msg('Attribute not found')
                return my_res.to_dict, my_res.code

            manifest = db.session.query(
                DataManifestModel).get(attribute.manifest_id)
            if not has_permission(manifest.project_code, "file_attribute", "*", "update"):
                my_res.set_code(EAPIResponseCode.forbidden)
                my_res.set_error_msg('Permission Denied')
                return my_res.to_dict, my_res.code

            try:
                response = requests.put(
                    ConfigClass.ENTITYINFO_SERVICE + f"attribute/{id}", json=data)
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling entityinfo service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

        @jwt_required()
        def delete(self, id):
            """
            Delete an attribute
            """
            my_res = APIResponse()
            attribute = db.session.query(DataAttributeModel).get(id)
            if not attribute:
                my_res.set_code(EAPIResponseCode.not_found)
                my_res.set_error_msg('Attribute not found')
                return my_res.to_dict, my_res.code
            manifest = db.session.query(
                DataManifestModel).get(attribute.manifest_id)
            if not has_permission(manifest.project_code, "file_attribute", "*", "delete"):
                my_res.set_code(EAPIResponseCode.forbidden)
                my_res.set_error_msg('Permission Denied')
                return my_res.to_dict, my_res.code
            try:
                response = requests.delete(
                    ConfigClass.ENTITYINFO_SERVICE + f"attribute/{id}")
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling entityinfo service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class FileManifest(Resource):
        """
        Edit a manifest attached to a file
        """
        @jwt_required()
        def put(self, file_geid):
            api_response = APIResponse()

            # data = request.get_json()

            # if not "global_entity_id" in data:
            #     api_response.set_code(EAPIResponseCode.bad_request)
            #     api_response.set_result(
            #         "Missing required parameter global_entity_id")
            #     return api_response.to_dict, api_response.code

            file_node = get_file_node_bygeid(file_geid)

            # Permissions check
            manifest = db.session.query(DataManifestModel).get(
                file_node["manifest_id"])
            if current_identity["role"] != "admin":
                if not has_permissions(manifest.id, file_node):
                    api_response.set_code(EAPIResponseCode.forbidden)
                    api_response.set_result("Permission Denied")
                    return api_response.to_dict, api_response.code

            if is_greenroom(file_node):
                zone = "greenroom"
            else:
                zone = "core"
            if not has_permission(manifest.project_code, 'file_attribute', zone, 'update'):
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("Permission Denied")
                return api_response.to_dict, api_response.code
            # payload = {
            #     "payload": request.get_json()
            # }
            try:
                response = requests.put(
                    ConfigClass.ENTITYINFO_SERVICE + f"files/{file_geid}/manifest", json=request.get_json())
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling entityinfo service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class ValidateManifest(Resource):
        """
        Validate the input to attach a file manifest
        """
        @jwt_required()
        @permissions_check('file_attribute_template', '*', 'attach')
        def post(self):
            data = request.get_json()
            try:
                response = requests.post(
                    ConfigClass.ENTITYINFO_SERVICE + "files/manifest/validate", json=data)
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling entityinfo service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class ImportManifest(Resource):
        @jwt_required()
        @permissions_check("file_attribute_template", "*", "import")
        def post(self):
            api_response = APIResponse()
            data = request.get_json()
            try:
                response = requests.post(
                    ConfigClass.ENTITYINFO_SERVICE + "manifest/file/import", json=data)
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling entityinfo service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class ExportManifest(Resource):
        @jwt_required()
        def get(self):
            api_response = APIResponse()
            manifest_id = request.args.get("manifest_id")
            response_data = {
                "attributes": []
            }
            if not manifest_id:
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_result(f"Missing required field manifest_id")
                return api_response.to_dict, api_response.code

            manifest = db.session.query(DataManifestModel).get(manifest_id)
            if not manifest:
                api_response.set_code(EAPIResponseCode.not_found)
                api_response.set_result(f"Maniefst not found")
                return api_response.to_dict, api_response.code

            if not has_permission(manifest.project_code, "file_attribute_template", "*", "export"):
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("Permission Denied")
                return api_response.to_dict, api_response.code

            try:
                response = requests.get(
                    ConfigClass.ENTITYINFO_SERVICE + "manifest/file/export", params={"manifest_id": manifest_id})
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling entityinfo service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class FileManifestQuery(Resource):
        @jwt_required()
        def post(self):
            api_response = APIResponse()
            required_fields = ["geid_list"]
            data = request.get_json()
            if not "geid_list" in data:
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_result(f"Missing required field: geid_list")
                return api_response.to_dict, api_response.code

            geid_list = data.get("geid_list")
            lineage_view = data.get("lineage_view")

            results = {}
            for geid in geid_list:
                file_node = get_file_node_bygeid(geid)
                if not file_node:
                    file_node = get_trashfile_node_bygeid(geid)

                if file_node and file_node.get("manifest_id"):
                    if not has_permissions(file_node["manifest_id"], file_node) and not lineage_view:
                        api_response.set_code(EAPIResponseCode.forbidden)
                        api_response.set_result(f"Permission denied")
                        return api_response.to_dict, api_response.code
                    attributes = []
                    manifest_id = file_node["manifest_id"]
                    manifest = db.session.query(
                        DataManifestModel).get(manifest_id)
                    if is_greenroom(file_node):
                        zone = "greenroom"
                    else:
                        zone = "core"
                    if not has_permission(manifest.project_code, 'file_attribute_template', zone, 'view'):
                        api_response.set_code(EAPIResponseCode.forbidden)
                        api_response.set_result("Permission Denied")
                        return api_response.to_dict, api_response.code
            try:
                response = requests.post(
                    ConfigClass.ENTITYINFO_SERVICE + "manifest/query", json=data)
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling entityinfo service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class AttachAttributes(Resource):
        @jwt_required()
        def post(self):
            api_response = APIResponse()
            required_fields = ["manifest_id", "global_entity_id",
                               "attributes", "inherit", "project_code"]
            data = request.get_json()
            # Check required fields
            for field in required_fields:
                if not field in data:
                    api_response.set_code(EAPIResponseCode.bad_request)
                    api_response.set_result(f"Missing required field: {field}")
                    return api_response.to_dict, api_response.code

            global_entity_id = data.get('global_entity_id')
            project_code = data.get('project_code')

            project_role = 'admin'
            if current_identity['role'] != 'admin':
                try:
                    project_role = get_project_permissions(
                        project_code, current_identity["user_id"])
                except Exception as e:
                    api_response.set_code(EAPIResponseCode.forbidden)
                    api_response.set_result(
                        f"User do not have access to this project")
                    return api_response.to_dict, api_response.code

                for geid in global_entity_id:
                    file_node = get_file_node_bygeid(geid)

                    if not file_node:
                        folder_node = get_folder_node_bygeid(geid)

                        if not folder_node:
                            api_response.set_code(EAPIResponseCode.not_found)
                            api_response.set_result(f"File/Folder not found")
                            return api_response.to_dict, api_response.code

                        root_folder = folder_node["display_path"].split("/")[0]

                        if project_role == 'collaborator':
                            if ConfigClass.CORE_ZONE_LABEL not in folder_node['labels'] and root_folder != current_identity['username']:
                                api_response.set_code(
                                    EAPIResponseCode.forbidden)
                                api_response.set_result(f"Permission denied")
                                return api_response.to_dict, api_response.code
                        elif project_role == 'contributor':
                            if root_folder != current_identity['username']:
                                api_response.set_code(
                                    EAPIResponseCode.forbidden)
                                api_response.set_result(f"Permission denied")
                                return api_response.to_dict, api_response.code
                    else:
                        root_folder = file_node["display_path"].split("/")[0]
                        if project_role == 'collaborator':
                            if ConfigClass.CORE_ZONE_LABEL not in file_node['labels'] and root_folder != current_identity['username']:
                                api_response.set_code(
                                    EAPIResponseCode.forbidden)
                                api_response.set_result(f"Permission denied")
                                return api_response.to_dict, api_response.code
                        elif project_role == 'contributor':
                            if root_folder != current_identity['username']:
                                api_response.set_code(
                                    EAPIResponseCode.forbidden)
                                api_response.set_result(f"Permission denied")
                                return api_response.to_dict, api_response.code
            else:
                for geid in global_entity_id:
                    file_node = get_file_node_bygeid(geid)

                    if not file_node:
                        folder_node = get_folder_node_bygeid(geid)

                        if not folder_node:
                            api_response.set_code(EAPIResponseCode.not_found)
                            api_response.set_result(f"File/Folder not found")
                            return api_response.to_dict, api_response.code

            post_data = {
                "manifest_id": data["manifest_id"],
                "global_entity_id": global_entity_id,
                "attributes": data["attributes"],
                "inherit": data["inherit"],
                "project_role": project_role,
                "username": current_identity['username']
            }

            res = requests.post(ConfigClass.ENTITYINFO_SERVICE +
                                'files/attributes/attach', json=post_data)

            print(post_data)
            if res.status_code != 200:
                _logger.error('Attach attribtues failed: {}'.format(res.text))

                api_response.set_code(res.status_code)
                api_response.set_result(res.text)
                return api_response.to_dict, api_response.code

            api_response.set_result(res.json())
            return api_response.to_dict, api_response.code
