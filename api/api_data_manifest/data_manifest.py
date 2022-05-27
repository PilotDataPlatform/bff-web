import requests

from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource
from common import LoggerFactory

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
from models.api_response import APIResponse, EAPIResponseCode
from resources.error_handler import APIException
from resources.swagger_modules import data_manifests, data_manifests_return
from services.meta import get_entity_by_id
from services.permissions_service.decorators import permissions_check
from services.permissions_service.utils import get_project_role, has_permission

from .utils import has_permissions, is_greenroom

api_ns_data_manifests = module_api.namespace(
    'Attribute Templates Restful', description='For data attribute templates feature', path='/v1')
api_ns_data_manifest = module_api.namespace(
    'Attribute Templates Restful', description='For data attribute templates feature', path='/v1')

_logger = LoggerFactory('api_data_manifest').get_logger()


class APIDataManifest(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_data_manifests.add_resource(
            self.RestfulManifests, '/data/manifests')
        api_ns_data_manifest.add_resource(
            self.RestfulManifest, '/data/manifest/<manifest_id>')
        api_ns_data_manifest.add_resource(self.FileAttributes, '/file/<file_geid>/manifest')
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
            List attribute templates by project_code
            """
            try:
                response = requests.get(
                    ConfigClass.METADATA_SERVICE + 'template/', params=request.args)
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling metadata service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

        @jwt_required()
        @permissions_check('file_attribute_template', '*', 'create')
        def post(self):
            """
            Create a new attribute template
            """
            try:
                response = requests.post(
                    ConfigClass.METADATA_SERVICE + 'template/', json=request.get_json())
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling metadata service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class RestfulManifest(Resource):
        @jwt_required()
        def get(self, manifest_id):
            """
            Get an attribute template by id
            """
            my_res = APIResponse()
            try:
                response = requests.get(
                    ConfigClass.METADATA_SERVICE + f'template/{manifest_id}/')
                res = response.json()['result']
                if not res:
                    my_res.set_code(EAPIResponseCode.not_found)
                    my_res.set_error_msg('Attribute template not found')
                    return my_res.to_dict, my_res.code

                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling metadata service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

        @jwt_required()
        def put(self, manifest_id):
            """
            Update attributes of template by id
            """
            my_res = APIResponse()
            data = request.get_json()
            project_code = data.get('project_code')

            # Permissions check
            if not has_permission(project_code, 'file_attribute_template', '*', 'update'):
                my_res.set_code(EAPIResponseCode.forbidden)
                my_res.set_result("Permission Denied")
                return my_res.to_dict, my_res.code

            try:
                params = {'id': manifest_id}
                response = requests.put(
                    ConfigClass.METADATA_SERVICE + 'template/', params=params, json=data)
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling metadata service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

        @jwt_required()
        def delete(self, manifest_id):
            """
            Delete an attribute template
            """
            my_res = APIResponse()
            data = request.get_json()
            project_code = data.get('project_code')

            # Permissions check
            if not has_permission(project_code, 'file_attribute_template', '*', 'delete'):
                my_res.set_code(EAPIResponseCode.forbidden)
                my_res.set_result("Permission Denied")
                return my_res.to_dict, my_res.code

            try:
                params = {'id': manifest_id}
                response = requests.delete(ConfigClass.METADATA_SERVICE + 'template/', params=params)
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling metadata service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class FileAttributes(Resource):
        """
        Update attributes of template attached to a file
        """

        @jwt_required()
        def put(self, file_geid):
            api_response = APIResponse()

            entity = get_entity_by_id(file_geid)
            if entity["extended"]["extra"].get("attributes"):
                template_id = list(entity["extended"]["extra"]["attributes"].keys())[0]
            else:
                raise APIException(
                    status_code=EAPIResponseCode.bad_request.value,
                    error_msg="File doesn't have an attached template"
                )
            # Permissions check
            if current_identity["role"] != "admin":
                if entity['owner'] != current_identity["username"]:
                    api_response.set_code(EAPIResponseCode.forbidden)
                    api_response.set_result("Permission Denied")
                    return api_response.to_dict, api_response.code

            if is_greenroom(entity):
                zone = "greenroom"
            else:
                zone = "core"
            if not has_permission(entity['container_code'], 'file_attribute', zone, 'update'):
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("Permission Denied")
                return api_response.to_dict, api_response.code

            try:
                params = {'id': entity['id']}
                attributes_update = request.get_json()

                payload = {
                    'parent': entity['parent'],
                    'parent_path': entity['parent_path'],
                    'type': 'file',
                    "attribute_template_id": template_id,
                    "attributes": attributes_update

                }
                response = requests.put(
                    ConfigClass.METADATA_SERVICE + 'item/', params=params, json=payload)

                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling metadata service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class ImportManifest(Resource):
        """
        Import attribute template from portal as JSON
        """

        @jwt_required()
        @permissions_check("file_attribute_template", "*", "import")
        def post(self):
            data = request.get_json()
            try:
                payload = {
                    'name': data['name'],
                    'project_code': data['project_code'],
                    'attributes': data['attributes']
                }
                response = requests.post(
                    ConfigClass.METADATA_SERVICE + 'template/', json=payload)
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling metadata service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class ExportManifest(Resource):
        """
        Export attribute template from portal as JSON
        """

        @jwt_required()
        def get(self):
            api_response = APIResponse()
            template_id = request.args.get("manifest_id")
            if not template_id:
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_result(f"Missing required field template_id")
                return api_response.to_dict, api_response.code

            try:
                response = requests.get(
                    ConfigClass.METADATA_SERVICE + f'template/{template_id}/')
                if not response:
                    api_response.set_code(EAPIResponseCode.not_found)
                    api_response.set_error_msg('Attribute template not found')
                    return api_response.to_dict, api_response.code

                template = response.json()['result'][0]
                if not has_permission(template['project_code'], "file_attribute_template", "*", "export"):
                    api_response.set_code(EAPIResponseCode.forbidden)
                    api_response.set_result("Permission Denied")
                    return api_response.to_dict, api_response.code
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f"Error when calling metadata service: {str(e)}")
                error_msg = {
                    "result": str(e)
                }
                return error_msg, 500

    class FileManifestQuery(Resource):
        """
        List template attributes for files
        """

        @jwt_required()
        def post(self):
            api_response = APIResponse()
            data = request.get_json()
            if "geid_list" not in data:
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_result(f"Missing required field: geid_list")
                return api_response.to_dict, api_response.code

            geid_list = data.get("geid_list")
            lineage_view = data.get("lineage_view")
            results = {}
            try:
                for geid in geid_list:
                    entity = get_entity_by_id(geid)
                    entity_attributes = entity["extended"]["extra"].get("attributes")
                    if entity_attributes:
                        template_id = list(entity["extended"]["extra"]["attributes"].keys())[0]
                        if not has_permissions(template_id, entity) and not lineage_view:
                            api_response.set_code(EAPIResponseCode.forbidden)
                            api_response.set_result(f"Permission denied")
                            return api_response.to_dict, api_response.code
                        if is_greenroom(entity):
                            zone = "greenroom"
                        else:
                            zone = "core"
                        if not has_permission(entity['container_code'], 'file_attribute_template', zone, 'view'):
                            api_response.set_code(EAPIResponseCode.forbidden)
                            api_response.set_result("Permission Denied")
                            return api_response.to_dict, api_response.code
                        response = requests.get(ConfigClass.METADATA_SERVICE + f'template/{template_id}/')
                        if response.status_code != 200:
                            api_response.set_code(EAPIResponseCode.not_found)
                            api_response.set_error_msg('Attribute template not found')
                            return api_response.to_dict, api_response.code
                        else:
                            attributes = []
                            template_name = response.json()['result']['name']
                            attribute = {'template_name': template_name,
                                         'template_id': template_id,
                                         'attributes': entity_attributes[template_id]}
                            attributes.append(attribute)
                        results[geid] = attributes
                    else:
                        results[geid] = {}
                return results, EAPIResponseCode.success.value
            except Exception as e:
                _logger.error(f"Error when calling metadata service: {str(e)}")
                error_msg = {"result": str(e)}
                return error_msg, 500

    class AttachAttributes(Resource):
        """
        Attach attributes to files or folders (bequeath)
        """
        @jwt_required()
        def post(self):
            api_response = APIResponse()
            required_fields = ["manifest_id", "item_ids", "attributes", "project_code"]
            data = request.get_json()
            payload = {'items': []}
            file_ids = []
            responses = []

            # Check required fields
            for field in required_fields:
                if field not in data:
                    api_response.set_code(EAPIResponseCode.bad_request)
                    api_response.set_result(f"Missing required field: {field}")
                    return api_response.to_dict, api_response.code

            item_ids = data.get('item_ids')
            project_code = data.get('project_code')
            items = []
            try:
                if current_identity['role'] != 'admin':
                    project_role = get_project_role(project_code)
                    if not project_role:
                        api_response.set_code(EAPIResponseCode.forbidden)
                        api_response.set_result(f"User does not have access to this project")
                        return api_response.to_dict, api_response.code

                    for item in item_ids:
                        entity = get_entity_by_id(item)
                        root_folder = entity["parent_path"].split(".")[0]
                        zone = "greenroom" if entity["zone"] == 1 else "core"
                        if project_role == 'collaborator':
                            if zone == "greenroom" and root_folder != current_identity['username']:
                                api_response.set_code(EAPIResponseCode.forbidden)
                                api_response.set_result(f"Permission denied")
                                return api_response.to_dict, api_response.code
                        elif project_role == 'contributor':
                            if root_folder != current_identity['username']:
                                api_response.set_code(EAPIResponseCode.forbidden)
                                api_response.set_result(f"Permission denied")
                                return api_response.to_dict, api_response.code
                        items.append(entity)

                for item in items:
                    if item['type'] == 'folder':
                        params = {'id': item['id']}
                        update = {'attribute_template_id': data['manifest_id'], 'attributes': data['attributes']}
                        response = requests.put(
                            ConfigClass.METADATA_SERVICE + 'items/batch/bequeath/', params=params, json=update)
                        if response.status_code != 200:
                            _logger.error('Attaching attributes failed: {}'.format(response.text))
                            api_response.set_code(response.status_code)
                            api_response.set_result(response.text)
                            return api_response.to_dict, api_response.code
                        responses.append(response.json()['result'])
                    else:
                        update = {
                            'parent': item['parent'],
                            'parent_path': item['parent_path'],
                            'type': item['type'],
                            "attribute_template_id": data['manifest_id'],
                            "attributes": data['attributes']
                        }
                        payload['items'].append(update)
                        file_ids.append(item['id'])
                if file_ids:
                    params = {'ids': file_ids}
                    response = requests.put(
                        ConfigClass.METADATA_SERVICE + 'items/batch/', params=params, json=payload)
                    if response.status_code != 200:
                        _logger.error('Attaching attributes failed: {}'.format(response.text))
                        api_response.set_code(response.status_code)
                        api_response.set_result(response.text)
                        return api_response.to_dict, api_response.code
                    responses.append(response.json()['result'])

                api_response.set_result(responses)
                return api_response.to_dict, api_response.code
            except Exception as e:
                _logger.error(f"Error when calling metadata service: {str(e)}")
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result(f"Error when calling metadata service: {str(e)}")
                return api_response.to_dict, api_response.code