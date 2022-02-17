from flask_restx import Api, Resource, fields
from flask_jwt import jwt_required, current_identity
from flask import request

from services.neo4j_service.neo4j_client import Neo4jClient
from services.logger_services.logger_factory_service import SrvLoggerFactory
from models.api_meta_class import MetaAPI
from models.api_response import APIResponse, EAPIResponseCode
from api import module_api
from .utils import check_dataset_permissions
from config import ConfigClass
import requests

api_resource = module_api.namespace('DatasetProxy', description='Folder  API', path='/v1/dataset/')

_logger = SrvLoggerFactory('api_versions').get_logger()

class APIDatasetFolder(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(self.DatasetFolder, '/<dataset_geid>/folder')

    class DatasetFolder(Resource):
        @jwt_required()
        def post(self, dataset_geid):
            _logger.info(f"POST dataset folder proxy")
            api_response = APIResponse()
            valid, response = check_dataset_permissions(dataset_geid)
            if not valid:
                return response.to_dict, response.code

            payload = {
                "username": current_identity["username"],
                **request.get_json()
            }
            try:
                response = requests.post(ConfigClass.DATASET_SERVICE + f"dataset/{dataset_geid}/folder", json=payload)
                print(ConfigClass.DATASET_SERVICE)
            except Exception as e:
                _logger.info(f"Error calling dataset service: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataset service: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code
