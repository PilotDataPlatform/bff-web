from flask_restx import Api, Resource, fields
from flask_jwt import jwt_required, current_identity
from flask import request

from resources.utils import get_project_permissions
from services.neo4j_service.neo4j_client import Neo4jClient
from services.permissions_service.utils import has_permission, get_project_code_from_request
from services.logger_services.logger_factory_service import SrvLoggerFactory
from models.api_meta_class import MetaAPI
from api import module_api
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode

import requests

api_resource = module_api.namespace('Archive', description='Archive API', path='/v1/archive')

_logger = SrvLoggerFactory('api_archive').get_logger()

class APIArchive(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(self.Archive, '/')

    class Archive(Resource):
        @jwt_required()
        def get(self):
            """
             Get a single resource request
            """
            _logger.info(f"GET archive called in bff")
            api_response = APIResponse()
            data = request.args
            neo4j_client = Neo4jClient()
            if not "project_geid" in data:
                _logger.error(f"Missing required parameter project_geid")
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_result("Missing required parameter project_geid")
                return api_response.to_dict, api_response.code

            # Get the File node from neo4j
            response = neo4j_client.node_query("File", {"global_entity_id": data["file_geid"]}) 
            if not response.get("result"):
                _logger.error(f"File not found with geid {entity}")
                api_response.set_code(EAPIResponseCode.not_found)
                api_response.set_result("File not found")
                return api_response.to_dict, api_response.code
            file_node = response.get("result")[0]
            if "Greenroom" in file_node["labels"]:
                zone = 'greenroom'
            else:
                zone = 'core'

            project_code = get_project_code_from_request({})
            if not has_permission(project_code, 'file', zone, 'view'):
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("Permission Denied")
                return api_response.to_dict, api_response.code

            if not self.has_file_permissions(project_code, file_node):
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("Permission Denied")
                return api_response.to_dict, api_response.code

            try:
                response = requests.get(ConfigClass.DATA_UTILITY_SERVICE + "archive", params=data)
            except Exception as e:
                _logger.info(f"Error calling dataops gr: {str(e)}")
                return response.json(), response.status_code
            return response.json(), response.status_code

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
