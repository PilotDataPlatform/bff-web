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
import requests
from common import ProjectClientSync


api_ns_report = module_api.namespace(
    'Announcement', description='Announcement API', path='/v1')


class APIAnnouncement(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_report.add_resource(
            self.AnnouncementRestful, '/announcements')

    class AnnouncementRestful(Resource):
        @jwt_required()
        @permissions_check("announcement", "*", "view")
        def get(self):
            api_response = APIResponse()
            data = request.args
            if not data.get("project_code"):
                api_response.set_error_msg("Missing project code")
                api_response.set_code(EAPIResponseCode.bad_request)
                return api_response.to_dict, api_response.code

            response = requests.get(ConfigClass.NOTIFY_SERVICE + "/v1/announcements", params=data)
            if response.status_code != 200:
                api_response.set_error_msg(response.json())
                return api_response.to_dict, response.status_code
            api_response.set_result(response.json())
            return api_response.to_dict, response.status_code

        @jwt_required()
        @permissions_check("announcement", "*", "create")
        def post(self):
            api_response = APIResponse()
            data = request.get_json()
            if not data.get("project_code"):
                api_response.set_error_msg("Missing project code")
                api_response.set_code(EAPIResponseCode.bad_request)
                return api_response.to_dict, api_response.code

            project_client = ProjectClientSync(
                ConfigClass.PROJECT_SERVICE,
                ConfigClass.REDIS_URL
            )
            # will 404 if project doesn't exist
            project_client.get(code=data["project_code"])

            data["publisher"] = current_identity["username"]
            response = requests.post(ConfigClass.NOTIFY_SERVICE + "/v1/announcements", json=data)
            if response.status_code != 200:
                api_response.set_error_msg(response.json()["error_msg"])
                response_dict = api_response.to_dict
                response_dict["code"] = response.status_code
                return response_dict, response.status_code
            api_response.set_result(response.json())
            return api_response.to_dict, response.status_code

