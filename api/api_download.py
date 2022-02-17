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
from resources.utils import get_project_permissions
from services.logger_services.logger_factory_service import SrvLoggerFactory
from services.neo4j_service.neo4j_client import Neo4jClient
from services.permissions_service.utils import has_permission

api_resource = module_api.namespace('Dataset Download', description='Dataset Download API', path='/v2/dataset')
api_resource_download = module_api.namespace('Download', description='Dataset Download API', path='/v2/download')

_logger = SrvLoggerFactory('api_download').get_logger()


class APIDatasetDownload(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(self.DatasetDownload, '/download/pre')
        api_resource_download.add_resource(self.Download, '/pre')

    class Download(Resource):
        @jwt_required()
        def post(self):
            api_response = APIResponse()
            payload = request.get_json()
            neo4j_client = Neo4jClient()
            zone = "core"
            if payload.get("dataset_geid"):
                # Get Dataset
                response = neo4j_client.node_query("Dataset", {"global_entity_id": payload.get("dataset_geid")})
                if not response.get("result"):
                    _logger.error(f"Dataset not found with geid {payload.get('dataset_geid')}")
                    api_response.set_code(EAPIResponseCode.not_found)
                    api_response.set_result("Dataset not found")
                    return api_response.to_dict, api_response.code
                dataset_node = response.get("result")[0]

                # Get file or folder node
                for file in payload.get("files"):
                    response = neo4j_client.node_query("File", {"global_entity_id": file["geid"]})
                    if not response.get("result"):
                        response = neo4j_client.node_query("Folder", {"global_entity_id": file["geid"]})
                    if not response.get("result"):
                        _logger.error(f"File or folder not found with geid {file['geid']}")
                        api_response.set_code(EAPIResponseCode.not_found)
                        api_response.set_result("File or Folder not found")
                        return api_response.to_dict, api_response.code
                    entity_node = response.get("result")[0]

                # file must belong to dataset
                if dataset_node["code"] != entity_node["dataset_code"]:
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
                    response = neo4j_client.node_query("File", {"global_entity_id": file["geid"]})
                    if not response.get("result"):
                        response = neo4j_client.node_query("Folder", {"global_entity_id": file["geid"]})
                    if not response.get("result"):
                        _logger.error(f"File or folder not found with geid {file['geid']}")
                        api_response.set_code(EAPIResponseCode.not_found)
                        api_response.set_result("File or Folder not found")
                        return api_response.to_dict, api_response.code
                    entity_node = response.get("result")[0]

                    if "Greenroom" in entity_node["labels"]:
                        zone = "greenroom"
                    else:
                        zone = "core"

                    if not has_permission(entity_node["project_code"], "file", zone, "download"):
                        api_response.set_code(EAPIResponseCode.forbidden)
                        api_response.set_error_msg("Permission Denied")
                        return api_response.to_dict, api_response.code

                    if not self.has_file_permissions(entity_node["project_code"], entity_node):
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
            if current_identity["role"] != "admin":
                role = get_project_permissions(project_code, current_identity["user_id"])
                if role != "admin":
                    root_folder = file_node["display_path"].split("/")[0]
                    if role == "contributor":
                        # contrib must own the file to attach manifests
                        if root_folder != current_identity["username"]:
                            return False
                    elif role == "collaborator":
                        if "Greenroom" in file_node.get("labels"):
                            if root_folder != current_identity["username"]:
                                return False
            return True

    class DatasetDownload(Resource):
        @jwt_required()
        def post(self):
            api_response = APIResponse()
            payload = request.get_json()
            if "dataset_geid" not in payload:
                _logger.error(f"Missing required field dataset_geid")
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_error_msg("Missing required field dataset_geid")
                return api_response.to_dict, api_response.code

            _logger.error("test here for the proxy")

            neo4j_client = Neo4jClient()
            response = neo4j_client.node_query("Dataset", {"global_entity_id": payload.get("dataset_geid")})
            if not response.get("result"):
                _logger.error(f"Dataset not found with geid {payload.get('dataset_geid')}")
                api_response.set_code(EAPIResponseCode.not_found)
                api_response.set_result("Dataset not found")
                return api_response.to_dict, api_response.code
            dataset_node = response.get("result")[0]

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
