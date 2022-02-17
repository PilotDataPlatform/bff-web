from flask_restx import Api, Resource, fields
from flask_jwt import jwt_required, current_identity
from flask import request, Response

from services.neo4j_service.neo4j_client import Neo4jClient
from services.permissions_service.utils import has_permission, get_project_code_from_request
from services.logger_services.logger_factory_service import SrvLoggerFactory
from models.api_meta_class import MetaAPI
from api import module_api
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from resources.utils import get_project_permissions

import requests

api_resource = module_api.namespace('Preview', description='Preview API', path='/v1/<file_geid>/preview')

_logger = SrvLoggerFactory('api_preview').get_logger()


class APIPreview(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(self.Preview, '/')
        api_resource.add_resource(self.StreamPreview, '/stream')

    class Preview(Resource):
        @jwt_required()
        def get(self, file_geid):
            _logger.info(f"GET preview called in bff")
            api_response = APIResponse()

            data = request.args
            dataset_geid = data.get("dataset_geid")
            neo4j_client = Neo4jClient()
            response = neo4j_client.node_query("Dataset", {"global_entity_id": dataset_geid}) 
            if not response.get("result"):
                _logger.error(f"Dataset not found with geid {dataset_geid}")
                api_response.set_code(EAPIResponseCode.not_found)
                api_response.set_result("Dataset not found")
                return api_response.to_dict, api_response.code
            dataset_node = response.get("result")[0]

            response = neo4j_client.node_query("File", {"global_entity_id": file_geid}) 
            if not response.get("result"):
                _logger.error(f"File not found with geid {file_geid}")
                api_response.set_code(EAPIResponseCode.not_found)
                api_response.set_result("File not found")
                return api_response.to_dict, api_response.code
            file_node = response.get("result")[0]

            if dataset_node["code"] != file_node["dataset_code"]:
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("File doesn't belong to dataset, Permission Denied")
                return api_response.to_dict, api_response.code

            if dataset_node["creator"] != current_identity["username"]:
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("Permission Denied")
                return api_response.to_dict, api_response.code

            try:
                response = requests.get(ConfigClass.DATASET_SERVICE + f"{file_geid}/preview", params=data, \
                    headers=request.headers)
            except Exception as e:
                _logger.info(f"Error calling dataops gr: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataops gr: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

    class StreamPreview(Resource):
        @jwt_required()
        def get(self, file_geid):
            _logger.info(f"GET preview called in bff")
            api_response = APIResponse()

            data = request.args
            dataset_geid = data.get("dataset_geid")
            neo4j_client = Neo4jClient()
            response = neo4j_client.node_query("Dataset", {"global_entity_id": dataset_geid}) 
            if not response.get("result"):
                _logger.error(f"Dataset not found with geid {dataset_geid}")
                api_response.set_code(EAPIResponseCode.not_found)
                api_response.set_result("Dataset not found")
                return api_response.to_dict, api_response.code
            dataset_node = response.get("result")[0]

            response = neo4j_client.node_query("File", {"global_entity_id": file_geid}) 
            if not response.get("result"):
                _logger.error(f"File not found with geid {file_geid}")
                api_response.set_code(EAPIResponseCode.not_found)
                api_response.set_result("File not found")
                return api_response.to_dict, api_response.code
            file_node = response.get("result")[0]

            if dataset_node["code"] != file_node["dataset_code"]:
                _logger.error(f"File doesn't belong to dataset file: {file_geid}, dataset: {dataset_geid}")
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("File doesn't belong to dataset, Permission Denied")
                return api_response.to_dict, api_response.code

            if dataset_node["creator"] != current_identity["username"]:
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("Permission Denied")
                return api_response.to_dict, api_response.code

            try:
                response = requests.get(ConfigClass.DATASET_SERVICE + f"{file_geid}/preview/stream", params=data, stream=True)
                return Response(
                    response.iter_content(chunk_size=10*1025),
                    content_type=response.headers.get("Content-Type", "text/plain")
                )
            except Exception as e:
                _logger.info(f"Error calling dataset service: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataops gr: {str(e)}")
                return api_response.to_dict, api_response.code
