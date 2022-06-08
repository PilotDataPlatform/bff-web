import requests
from flask import request
from flask_jwt import current_identity
from flask_jwt import jwt_required
from flask_restx import Resource

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from common import LoggerFactory
from services.permissions_service.utils import has_permission, get_project_role
from services.meta import get_entity_by_id
from services.dataset import get_dataset_by_code


api_resource = module_api.namespace('Dataset Download', description='Dataset Download API', path='/v2/dataset')
api_resource_download = module_api.namespace('Download', description='Dataset Download API', path='/v2/download')

_logger = LoggerFactory('api_download').get_logger()


class APIDatasetDownload(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(self.DatasetDownload, '/download/pre')
        api_resource_download.add_resource(self.Download, '/pre')

    class Download(Resource):
        @jwt_required()
        def post(self):
            api_response = APIResponse()
            payload = request.get_json()
            zone = "core"
            if payload.get("container_type") == "dataset":
                dataset_node = get_dataset_by_code(payload.get("container_code"))

                # Get file or folder node
                for file in payload.get("files"):
                    entity_node = get_entity_by_id(file["id"])

                # file must belong to dataset
                if dataset_node["code"] != entity_node["container_code"]:
                    _logger.error(f"File doesn't belong to dataset file: {dataset_node['code']}, "
                                  f"dataset: {entity_node['dataset_code']}")
                    api_response.set_code(EAPIResponseCode.forbidden)
                    api_response.set_result("File doesn't belong to dataset, Permission Denied")
                    return api_response.to_dict, api_response.code

                # user must own dataset
                if dataset_node["creator"] != current_identity["username"]:
                    api_response.set_code(EAPIResponseCode.forbidden)
                    api_response.set_result("Permission Denied")
                    return api_response.to_dict, api_response.code
            else:
                for file in payload.get("files"):
                    entity_node = get_entity_by_id(file["id"])
                    zone = "greenroom" if entity_node["zone"] == 1 else "core"

                    if not has_permission(entity_node["container_code"], "file", zone, "download"):
                        api_response.set_code(EAPIResponseCode.forbidden)
                        api_response.set_error_msg("Permission Denied")
                        return api_response.to_dict, api_response.code

                    if not self.has_file_permissions(entity_node["container_code"], entity_node):
                        api_response.set_code(EAPIResponseCode.forbidden)
                        api_response.set_error_msg("Permission Denied")
                        return api_response.to_dict, api_response.code
            try:
                if zone == "core":
                    response = requests.post(
                        ConfigClass.DOWNLOAD_SERVICE_CORE_V2 + 'download/pre/', json=payload, headers=request.headers
                    )
                else:
                    response = requests.post(
                        ConfigClass.DOWNLOAD_SERVICE_GR_V2 + 'download/pre/', json=payload, headers=request.headers
                    )
                return response.json(), response.status_code
            except Exception as e:
                _logger.info("Error calling download service " + str(e))
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_error_msg("Error calling download service")
                return api_response.to_dict, api_response.code

        def has_file_permissions(self, project_code, file_node):
            zone = "greenroom" if file_node["zone"] == 1 else "core"
            if current_identity["role"] != "admin":
                role = get_project_role(project_code)
                if not role in ["admin", "platform_admin"]:
                    root_folder = file_node["parent_path"].split(".")[0]
                    if role == "contributor":
                        # contrib must own the file to attach manifests
                        if root_folder != current_identity["username"]:
                            return False
                    elif role == "collaborator":
                        if zone == "greenroom":
                            if root_folder != current_identity["username"]:
                                return False
            return True

    class DatasetDownload(Resource):
        @jwt_required()
        def post(self):
            api_response = APIResponse()
            payload = request.get_json()
            if "dataset_code" not in payload:
                _logger.error(f"Missing required field dataset_code")
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_error_msg("Missing required field dataset_code")
                return api_response.to_dict, api_response.code

            _logger.error("test here for the proxy")

            dataset_node = get_dataset_by_code(payload.get("dataset_code"))
            if dataset_node["creator"] != current_identity["username"]:
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("Permission Denied")
                return api_response.to_dict, api_response.code

            _logger.error("test here for the proxy")
            try:
                response = requests.post(
                    ConfigClass.DOWNLOAD_SERVICE_CORE_V2 + 'dataset/download/pre', json=payload, headers=request.headers
                )
                return response.json(), response.status_code
            except Exception as e:
                _logger.info("Error calling download service " + str(e))
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_error_msg("Error calling download service")
                return api_response.to_dict, api_response.code
