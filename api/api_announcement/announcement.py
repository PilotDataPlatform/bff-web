from flask_restx import Api, Resource, fields
from flask_jwt import jwt_required, current_identity
from models.api_meta_class import MetaAPI
from flask import request

from models.api_response import APIResponse, EAPIResponseCode
from api import module_api
from config import ConfigClass
from resources.utils import get_project_permissions
from services.permissions_service.decorators import permissions_check
import requests


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
            return api_response.to_dict, api_response.code

        @jwt_required()
        @permissions_check("announcement", "*", "create")
        def post(self):
            api_response = APIResponse()
            data = request.get_json()
            if not data.get("project_code"):
                api_response.set_error_msg("Missing project code")
                api_response.set_code(EAPIResponseCode.bad_request)
                return api_response.to_dict, api_response.code

            # Get Dataset
            response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/Container/query", json={"code": data["project_code"]})
            if not response.json():
                api_response.set_error_msg("Dataset not found")
                api_response.set_code(EAPIResponseCode.not_found)
                return api_response.to_dict, api_response.code
            dataset_id = response.json()[0]["id"]

            data["publisher"] = current_identity["username"]
            response = requests.post(ConfigClass.NOTIFY_SERVICE + "/v1/announcements", json=data)
            if response.status_code != 200:
                api_response.set_error_msg(response.json()["error_msg"])
                response_dict = api_response.to_dict
                response_dict["code"] = response.status_code
                return response_dict, response.status_code
            api_response.set_result(response.json())
            return api_response.to_dict, api_response.code

