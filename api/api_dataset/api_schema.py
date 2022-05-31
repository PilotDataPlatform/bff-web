from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from flask import request

from common import LoggerFactory
from models.api_meta_class import MetaAPI
from api import module_api
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
import requests
from .utils import check_dataset_permissions

api_resource = module_api.namespace('DatasetProxy', description='Versions API', path='/v1/dataset/')

_logger = LoggerFactory('api_schema').get_logger()


class APISchema(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(self.SchemaCreate, '/<dataset_id>/schema')
        api_resource.add_resource(self.Schema, '/<dataset_id>/schema/<schema_id>')
        api_resource.add_resource(self.SchemaList, '/<dataset_id>/schema/list')

    class SchemaCreate(Resource):
        @jwt_required()
        def post(self, dataset_id):
            api_response = APIResponse()
            valid, response = check_dataset_permissions(dataset_id)
            if not valid:
                return response.to_dict, response.code

            try:
                response = requests.post(ConfigClass.DATASET_SERVICE + "schema", json=request.get_json())
            except Exception as e:
                _logger.info(f"Error calling dataset service: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataset service: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

    class Schema(Resource):
        @jwt_required()
        def put(self, dataset_id, schema_id):
            api_response = APIResponse()
            valid, response = check_dataset_permissions(dataset_id)
            if not valid:
                return response.to_dict, response.code

            payload = request.get_json()
            payload["username"] = current_identity["username"]
            try:
                response = requests.put(ConfigClass.DATASET_SERVICE + f"schema/{schema_id}", json=payload)
            except Exception as e:
                _logger.info(f"Error calling dataset service: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataset service: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

        @jwt_required()
        def get(self, dataset_id, schema_id):
            api_response = APIResponse()
            valid, response = check_dataset_permissions(dataset_id)
            if not valid:
                return response.to_dict, response.code

            try:
                response = requests.get(ConfigClass.DATASET_SERVICE + f"schema/{schema_id}")
            except Exception as e:
                _logger.info(f"Error calling dataset service: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataset service: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

        @jwt_required()
        def delete(self, dataset_id, schema_id):
            api_response = APIResponse()
            valid, response = check_dataset_permissions(dataset_id)
            if not valid:
                return response.to_dict, response.code

            payload = request.get_json()
            payload["username"] = current_identity["username"]
            payload["dataset_geid"] = dataset_id
            try:
                response = requests.delete(ConfigClass.DATASET_SERVICE + f"schema/{schema_id}", json=payload)
            except Exception as e:
                _logger.info(f"Error calling dataset service: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataset service: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

    class SchemaList(Resource):
        @jwt_required()
        def post(self, dataset_id):
            api_response = APIResponse()
            valid, response = check_dataset_permissions(dataset_id)
            if not valid:
                return response.to_dict, response.code
            payload = request.get_json()
            payload["creator"] = current_identity["username"]
            payload["dataset_geid"] = dataset_id
            try:
                response = requests.post(ConfigClass.DATASET_SERVICE + "schema/list", json=payload)
            except Exception as e:
                _logger.info(f"Error calling dataset service: {str(e)}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f"Error calling dataset service: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code
