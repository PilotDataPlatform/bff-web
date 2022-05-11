from flask_restx import Api, Resource, fields
from flask_jwt import jwt_required, current_identity
from models.api_meta_class import MetaAPI
from flask import request

from models.api_response import APIResponse, EAPIResponseCode
from api import module_api
from config import ConfigClass
from services.permissions_service.decorators import permissions_check
from services.permissions_service.utils import get_project_role, get_project_code_from_request
from services.neo4j_service.neo4j_client import Neo4jClient
import requests

api_ns_report = module_api.namespace('CopyRequest', description='CopyRequest API', path='/v1/request')


class APICopyRequest(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_report.add_resource(self.CopyRequest, '/copy/<project_geid>')
        api_ns_report.add_resource(self.CopyRequestFiles, '/copy/<project_geid>/files')
        api_ns_report.add_resource(self.CopyRequestPending, '/copy/<project_geid>/pending-files')

    class CopyRequest(Resource):
        @jwt_required()
        @permissions_check("copyrequest", "*", "view")
        def get(self, project_geid):
            api_response = APIResponse()
            data = request.args.copy()
            code = get_project_code_from_request({"project_geid": project_geid})
            if get_project_role(code) == "collaborator":
                data["submitted_by"] = current_identity["username"]

            try:
                response = requests.get(ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_geid}", params=data)
            except Exception as e:
                api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

        @jwt_required()
        @permissions_check("copyrequest", "*", "create")
        def post(self, project_geid):
            api_response = APIResponse()
            data = request.get_json()

            if current_identity["role"] == "admin":
                # Platform admin can't create request
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_error_msg("Permission denied")
                return api_response.to_dict, api_response.code

            neo4j_client = Neo4jClient()
            response = neo4j_client.get_container_by_geid(project_geid)
            if not response.get("result"):
                error_msg = response.get("error_msg", "Neo4j error")
                _logger.error(f'Error fetching project from neo4j: {error_msg}')
                _res.set_code(response.get("code"))
                _res.set_error_msg(error_msg)
                return _res.to_dict, _res.code
            project_node = response.get("result")

            data["submitted_by"] = current_identity["username"]
            data["project_code"] = project_node["code"]
            try:
                response = requests.post(ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_geid}", json=data)
            except Exception as e:
                api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

        @jwt_required()
        @permissions_check("copyrequest", "*", "update")
        def put(self, project_geid):
            api_response = APIResponse()
            data = request.get_json()
            put_data = data.copy()
            put_data["username"] = current_identity["username"]

            try:
                response = requests.put(ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_geid}", json=put_data)
            except Exception as e:
                api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

    class CopyRequestFiles(Resource):
        @jwt_required()
        @permissions_check("copyrequest", "*", "view")
        def get(self, project_geid):
            api_response = APIResponse()
            data = request.args.copy()

            try:
                response = requests.get(ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_geid}/files", params=data)
            except Exception as e:
                api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

        @jwt_required()
        @permissions_check("copyrequest", "*", "update")
        def put(self, project_geid):
            api_response = APIResponse()
            data = request.get_json()
            post_data = data.copy()
            post_data["username"] = current_identity["username"]

            try:
                response = requests.put(
                    ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_geid}/files",
                    json=post_data,
                    headers=request.headers
                )
            except Exception as e:
                api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

        @jwt_required()
        @permissions_check("copyrequest", "*", "update")
        def patch(self, project_geid):
            api_response = APIResponse()
            data = request.get_json()
            post_data = data.copy()
            post_data["username"] = current_identity["username"]

            try:
                response = requests.patch(
                    ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_geid}/files",
                    json=post_data,
                    headers=request.headers
                )
            except Exception as e:
                api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

    class CopyRequestPending(Resource):
        @jwt_required()
        @permissions_check("copyrequest", "*", "update") # API is only used when admin is updating 
        def get(self, project_geid):
            api_response = APIResponse()
            try:
                response = requests.get(
                    ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_geid}/pending-files",
                    params=request.args,
                )
            except Exception as e:
                api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code
