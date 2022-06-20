# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from models.api_meta_class import MetaAPI
from flask import request

from models.api_response import APIResponse, EAPIResponseCode
from api import module_api
from config import ConfigClass
from services.permissions_service.decorators import permissions_check
from services.permissions_service.utils import get_project_role
import requests

api_ns_report = module_api.namespace('CopyRequest', description='CopyRequest API', path='/v1/request')


class APICopyRequest(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_report.add_resource(self.CopyRequest, '/copy/<project_code>')
        api_ns_report.add_resource(self.CopyRequestFiles, '/copy/<project_code>/files')
        api_ns_report.add_resource(self.CopyRequestPending, '/copy/<project_code>/pending-files')

    class CopyRequest(Resource):
        @jwt_required()
        @permissions_check("copyrequest", "*", "view")
        def get(self, project_code):
            api_response = APIResponse()
            data = request.args.copy()
            if get_project_role(project_code) == "collaborator":
                data["submitted_by"] = current_identity["username"]

            try:
                response = requests.get(ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}", params=data)
            except Exception as e:
                api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

        @jwt_required()
        @permissions_check("copyrequest", "*", "create")
        def post(self, project_code):
            api_response = APIResponse()
            data = request.get_json()

            if current_identity["role"] == "admin":
                # Platform admin can't create request
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_error_msg("Permission denied")
                return api_response.to_dict, api_response.code

            data["submitted_by"] = current_identity["username"]
            data["project_code"] = project_code
            try:
                response = requests.post(ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}", json=data)
            except Exception as e:
                api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

        @jwt_required()
        @permissions_check("copyrequest", "*", "update")
        def put(self, project_code):
            api_response = APIResponse()
            data = request.get_json()
            put_data = data.copy()
            put_data["username"] = current_identity["username"]

            try:
                response = requests.put(ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}", json=put_data)
            except Exception as e:
                api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

    class CopyRequestFiles(Resource):
        @jwt_required()
        @permissions_check("copyrequest", "*", "view")
        def get(self, project_code):
            api_response = APIResponse()
            data = request.args.copy()

            try:
                response = requests.get(ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}/files", params=data)
            except Exception as e:
                api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

        @jwt_required()
        @permissions_check("copyrequest", "*", "update")
        def put(self, project_code):
            api_response = APIResponse()
            data = request.get_json()
            post_data = data.copy()
            post_data["username"] = current_identity["username"]

            try:
                response = requests.put(
                    ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}/files",
                    json=post_data,
                    headers=request.headers
                )
            except Exception as e:
                api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

        @jwt_required()
        @permissions_check("copyrequest", "*", "update")
        def patch(self, project_code):
            api_response = APIResponse()
            data = request.get_json()
            post_data = data.copy()
            post_data["username"] = current_identity["username"]

            try:
                response = requests.patch(
                    ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}/files",
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
        def get(self, project_code):
            api_response = APIResponse()
            try:
                response = requests.get(
                    ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}/pending-files",
                    params=request.args,
                )
            except Exception as e:
                api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code
