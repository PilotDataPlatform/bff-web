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
from datetime import datetime

import requests
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
from models.api_response import APIResponse, EAPIResponseCode
from resources.error_handler import APIException
from services.permissions_service.utils import get_project_role

api_ns_report = module_api.namespace('Users', description='Users API', path='/v1')


class APIUsers(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_report.add_resource(self.UserRestful, '/users/<username>')

    class UserRestful(Resource):
        @jwt_required()
        def get(self, username):
            api_response = APIResponse()
            project_code = request.args.get("project_code")

            if current_identity["role"] != "admin" and current_identity["username"] != username:
                if not project_code:
                        api_response.set_error_msg("Username doesn't match current user")
                        api_response.set_code(EAPIResponseCode.forbidden)
                        return api_response.to_dict, api_response.code
                else:
                    if get_project_role(project_code) != "admin":
                        api_response.set_error_msg("Username doesn't match current user")
                        api_response.set_code(EAPIResponseCode.forbidden)
                        return api_response.to_dict, api_response.code

                    if not is_user_in_project(username, project_code):
                        api_response.set_error_msg("Permission Deneid")
                        api_response.set_code(EAPIResponseCode.forbidden)
                        return api_response.to_dict, api_response.code

            data = {
                "username": username,
            }
            response = requests.get(ConfigClass.AUTH_SERVICE + "admin/user", params=data)
            if not response.json():
                api_response.set_error_msg("User not found")
                api_response.set_code(EAPIResponseCode.not_found)
                return api_response
            response_json = response.json()["result"]
            response_json["name"] = response_json["username"]
            for key, value in response_json["attributes"].items():
                if "announcement_" in key:
                    response_json[key] = value

            create_time = response_json["createdTimestamp"]
            create_time = datetime.fromtimestamp(int(create_time/1000)).strftime("%Y-%m-%dT%H:%M:%S")
            response_json["createdTimestamp"] = create_time

            api_response.set_result(response_json)
            api_response.set_code(response.status_code)
            return api_response.to_dict, api_response.code

        @jwt_required()
        def put(self, username):
            api_response = APIResponse()
            data = request.get_json()
            if current_identity["username"] != username:
                api_response.set_error_msg("Username doesn't match current user")
                api_response.set_code(EAPIResponseCode.forbidden)
                return api_response.to_dict, api_response.code
            if len(data.items()) > 1:
                api_response.set_error_msg("Ton many parameters, only 1 announcement can be updated")
                api_response.set_code(EAPIResponseCode.bad_request)
                return api_response.to_dict, api_response.code

            for key, value in data.items():
                if not "announcement" in key:
                    api_response.set_error_msg("Invalid field, must have a announcement_ prefix")
                    api_response.set_code(EAPIResponseCode.bad_request)
                    return api_response.to_dict, api_response.code
                payload = {
                    "project_code": key.replace("announcement_", ""),
                    "announcement_pk": value,
                    "username": username,
                }
            response = requests.put(ConfigClass.AUTH_SERVICE + "admin/user", json=payload)
            return response.json(), response.status_code


def is_user_in_project(username: str, project_code: str) -> bool:
    response = requests.get(
        ConfigClass.AUTH_SERVICE + "admin/users/realm-roles",
        params={"username": username},
    )
    if response.status_code != 200:
        error_msg = "Error getting user from auth service: {response.json()}"
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)

    user_roles = response.json().get("result", [])
    user_project_role = None
    for role in user_roles:
        if project_code in role.get("name"):
            user_project_role = role["name"]
            break
    if not user_project_role:
        return False
    return True
