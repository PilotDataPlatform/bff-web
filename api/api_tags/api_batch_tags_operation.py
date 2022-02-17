from flask import request
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from models.api_response import APIResponse, EAPIResponseCode
from services.logger_services.logger_factory_service import SrvLoggerFactory
from config import ConfigClass
from api import module_api
from models.api_meta_class import MetaAPI
from services.permissions_service.utils import has_permission, get_project_code_from_request, get_project_role
from services.neo4j_service.neo4j_client import Neo4jClient
import json
import requests

_logger = SrvLoggerFactory('batch_api_tags').get_logger()
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
            neo4j_client = Neo4jClient()
            for entity in data.get("entity"):
                # Get the File or Folder node from neo4j
                response = neo4j_client.node_query(
                    "File", {"global_entity_id": entity})
                if not response.get("result"):
                    response = neo4j_client.node_query(
                        "Folder", {"global_entity_id": entity})
                if not response.get("result"):
                    _logger.error(
                        f"File or folder not found with geid {entity}")
                    _res.set_code(EAPIResponseCode.not_found)
                    _res.set_result("File or Folder not found")
                    return _res.to_dict, _res.code
                entity_node = response.get("result")[0]
                root_folder = entity_node["display_path"].split("/")[0]

                if "Greenroom" in entity_node["labels"]:
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
