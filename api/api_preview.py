import requests
from common import LoggerFactory
from flask import Response, request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
from models.api_response import APIResponse, EAPIResponseCode
from services.dataset import get_dataset_by_id
from services.meta import get_entity_by_id

api_resource = module_api.namespace('Preview', description='Preview API', path='/v1/<file_geid>/preview')

_logger = LoggerFactory('api_preview').get_logger()


class APIPreview(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(self.Preview, '/')
        api_resource.add_resource(self.StreamPreview, '/stream')

    class Preview(Resource):
        @jwt_required()
        def get(self, file_geid):
            _logger.info("GET preview called in bff")
            api_response = APIResponse()

            data = request.args
            dataset_geid = data.get("dataset_geid")
            dataset_node = get_dataset_by_id(dataset_geid)
            file_node = get_entity_by_id(file_geid)

            if dataset_node["code"] != file_node["container_code"]:
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("File doesn't belong to dataset, Permission Denied")
                return api_response.to_dict, api_response.code

            if dataset_node["creator"] != current_identity["username"]:
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("Permission Denied")
                return api_response.to_dict, api_response.code

            try:
                response = requests.get(
                    ConfigClass.DATASET_SERVICE + f"{file_geid}/preview",
                    params=data,
                    headers=request.headers
                )
            except Exception as e:
                _logger.info(f"Error calling dataops gr: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataops gr: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

    class StreamPreview(Resource):
        @jwt_required()
        def get(self, file_geid):
            _logger.info("GET preview called in bff")
            api_response = APIResponse()

            data = request.args
            dataset_geid = data.get("dataset_geid")
            dataset_node = get_dataset_by_id(dataset_geid)
            file_node = get_entity_by_id(file_geid)

            if dataset_node["code"] != file_node["container_code"]:
                _logger.error(f"File doesn't belong to dataset file: {file_geid}, dataset: {dataset_geid}")
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("File doesn't belong to dataset, Permission Denied")
                return api_response.to_dict, api_response.code

            if dataset_node["creator"] != current_identity["username"]:
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("Permission Denied")
                return api_response.to_dict, api_response.code

            try:
                response = requests.get(
                    ConfigClass.DATASET_SERVICE + f"{file_geid}/preview/stream",
                    params=data,
                    stream=True
                )
                return Response(
                    response.iter_content(chunk_size=10*1025),
                    content_type=response.headers.get("Content-Type", "text/plain")
                )
            except Exception as e:
                _logger.info(f"Error calling dataset service: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataops gr: {str(e)}")
                return api_response.to_dict, api_response.code
