from flask_restx import Api, Resource, fields
from flask_jwt import jwt_required, current_identity
from flask import request

from services.neo4j_service.neo4j_client import Neo4jClient
from services.logger_services.logger_factory_service import SrvLoggerFactory
from models.api_meta_class import MetaAPI
from api import module_api
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
import requests
from .utils import check_dataset_permissions

api_resource = module_api.namespace('DatasetProxy', description='Versions API', path='/v1/dataset/')

_logger = SrvLoggerFactory('api_versions').get_logger()


class APIVersions(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(self.Publish, '/<dataset_geid>/publish')
        api_resource.add_resource(self.PublishStatus, '/<dataset_geid>/publish/status')
        api_resource.add_resource(self.DownloadPre, '/<dataset_geid>/download/pre')
        api_resource.add_resource(self.DatasetVersions, '/<dataset_geid>/versions')

    class Publish(Resource):
        @jwt_required()
        def post(self, dataset_geid):
            api_response = APIResponse()
            valid, response = check_dataset_permissions(dataset_geid)
            if not valid:
                return response.to_dict, response.code

            try:
                response = requests.post(ConfigClass.DATASET_SERVICE + f"dataset/{dataset_geid}/publish", json=request.get_json())
            except Exception as e:
                _logger.info(f"Error calling dataset service: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataset service: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

    class PublishStatus(Resource):
        @jwt_required()
        def get(self, dataset_geid):
            api_response = APIResponse()
            valid, response = check_dataset_permissions(dataset_geid)
            if not valid:
                return response.to_dict, response.code

            try:
                response = requests.get(ConfigClass.DATASET_SERVICE + f"dataset/{dataset_geid}/publish/status", params=request.args)
            except Exception as e:
                _logger.info(f"Error calling dataset service: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataset service: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

    class DownloadPre(Resource):
        @jwt_required()
        def get(self, dataset_geid):
            api_response = APIResponse()
            valid, response = check_dataset_permissions(dataset_geid)
            if not valid:
                return response.to_dict, response.code

            try:
                response = requests.get(ConfigClass.DATASET_SERVICE + f"dataset/{dataset_geid}/download/pre", \
                    params=request.args, headers=request.headers)
            except Exception as e:
                _logger.info(f"Error calling dataset service: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataset service: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

    class DatasetVersions(Resource):
        @jwt_required()
        def get(self, dataset_geid):
            api_response = APIResponse()
            valid, response = check_dataset_permissions(dataset_geid)
            if not valid:
                return response.to_dict, response.code

            try:
                response = requests.get(ConfigClass.DATASET_SERVICE + f"dataset/{dataset_geid}/versions", params=request.args)
            except Exception as e:
                _logger.info(f"Error calling dataset service: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataset service: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code
