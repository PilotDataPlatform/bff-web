from flask import request
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from models.api_response import APIResponse, EAPIResponseCode
from common import LoggerFactory
from config import ConfigClass
from api import module_api
from models.api_meta_class import MetaAPI
from services.permissions_service.utils import has_permission, get_project_code_from_request, get_project_role
from services.neo4j_service.neo4j_client import Neo4jClient
from services.meta import get_entity_by_id
import requests

_logger = LoggerFactory('batch_api_tags').get_logger()
api_ns = module_api.namespace(
    'Batch Tags API', description='Batch Tags API', path='/v2')


class APIBatchTagsV2(metaclass=MetaAPI):
    def api_registry(self):
        api_ns.add_resource(self.BatchTagsAPIV2, '/entity/tags')

    class BatchTagsAPIV2(Resource):
        @jwt_required()
        def post(self):
            _res = APIResponse()
            data = request.get_json()
            url = ConfigClass.DATA_UTILITY_SERVICE_v2 + 'entity/tags'
            project_code = get_project_code_from_request({})
            for entity in data.get("entity"):
                entity = get_entity_by_id(entity)
                root_folder = entity["parent_path"].split(".")[0]

                if entity["zone"] == 1:
                    zone = 'greenroom'
                else:
                    zone = 'core'

                if not has_permission(project_code, 'tags', zone, 'create'):
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_result("Permission Denied")
                    return _res.to_dict, _res.code
                role = get_project_role(project_code)
                if role == "contributor" and current_identity["username"] != root_folder:
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_result("Permission Denied")
                    return _res.to_dict, _res.code
                if role == "collaborator" and zone != "core" and current_identity["username"] != root_folder:
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_result("Permission Denied")
                    return _res.to_dict, _res.code

            try:
                response = requests.post(url, json=data)
                _logger.info(f"Batch operation successful : {response}")
                return response.json()
            except Exception as error:
                _logger.error(
                    f"Error while performing batch operation for tags : {error}")
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result(
                    "Error while performing batch operation for tags " + str(error))
                return _res.to_dict, _res.code
