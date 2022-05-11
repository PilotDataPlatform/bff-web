from flask_restx import Resource
from flask_jwt import jwt_required, current_identity

from services.permissions_service.utils import has_permission, get_project_code_from_request, get_project_role
from common import LoggerFactory
from models.api_meta_class import MetaAPI
from api import module_api
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from flask import request as f_request
import requests

api_resource = module_api.namespace('Archive', description='Archive API', path='/v1/archive')

_logger = LoggerFactory('api_archive').get_logger()


class APIArchive(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(self.Archive, '/')

    class Archive(Resource):
        @jwt_required()
        def get(self):
            """
             Get a single resource request
            """
            _logger.info("GET archive called in bff")
            api_response = APIResponse()
            data = f_request.args
            if "file_id" not in data:
                _logger.error("Missing required parameter file_id")
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_result("Missing required parameter file_id")
                return api_response.to_dict, api_response.code

            file_id = data["file_id"]
            # Retrieve file info from metadata service
            request = requests.get(f"{ConfigClass.METADATA_SERVICE}item/{file_id}")
            file_response = request.json()["result"]
            if not file_response:
                _logger.error(f"File not found with following geid: {file_id}")
                api_response.set_code(EAPIResponseCode.not_found)
                api_response.set_result("File not found")
                return api_response.to_dict, api_response.code

            if file_response["zone"] == 0:
                zone = 'greenroom'
            else:
                zone = 'core'

            project_code = file_response["container_code"]
            if not has_permission(project_code, 'file', zone, 'view'):
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("Permission Denied")
                return api_response.to_dict, api_response.code

            if not self.has_file_permissions(project_code, file_response):
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result("Permission Denied")
                return api_response.to_dict, api_response.code

            try:
                response = requests.get(ConfigClass.DATA_UTILITY_SERVICE + "archive", params={"file_id": file_id})
            except Exception as e:
                _logger.info(f"Error calling dataops gr: {str(e)}")
                return response.json(), response.status_code
            return response.json(), response.status_code

        def has_file_permissions(self, project_code, file_info):
            if current_identity["role"] != "admin":
                role = get_project_role(project_code)
                if role != "admin":
                    root_folder = file_info["parent_path"].split(".")[0]
                    if role == "contributor":
                        # contrib must own the file to attach manifests
                        if root_folder != current_identity["username"]:
                            return False
                    elif role == "collaborator":
                        if file_info["zone"] == 0:
                            if root_folder != current_identity["username"]:
                                return False
            return True
