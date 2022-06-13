import requests
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
from models.api_response import APIResponse, EAPIResponseCode
from services.permissions_service.decorators import permissions_check

api_ns = module_api.namespace('Workbench', description='Workbench API', path='/v1')


class APIWorkbench(metaclass=MetaAPI):
    def api_registry(self):
        api_ns.add_resource(self.WorkbenchRestful, '/<project_id>/workbench')

    class WorkbenchRestful(Resource):
        @jwt_required()
        @permissions_check("workbench", "*", "view")
        def get(self, project_id):
            api_response = APIResponse()
            payload = {
                "project_id": project_id,
            }
            try:
                response = requests.get(ConfigClass.PROJECT_SERVICE + "/v1/workbenches", params=payload)
                data = {i["resource"]: i for i in response.json()["result"]}
            except Exception as e:
                api_response.set_error_msg("Error calling project: " + str(e))
                api_response.set_code(EAPIResponseCode.internal_error)
                return api_response.to_dict, api_response.code
            api_response.set_result(data)
            api_response.set_code(response.status_code)
            return api_response.to_dict, api_response.code

        @jwt_required()
        @permissions_check("workbench", "*", "create")
        def post(self, project_id):
            api_response = APIResponse()
            data = request.get_json()
            payload = {
                "project_id": project_id,
                "resource": data.get("workbench_resource"),
                "deployed_by_user_id": current_identity["user_id"],
            }
            try:
                response = requests.post(ConfigClass.PROJECT_SERVICE + "/v1/workbenches", json=payload)
            except Exception as e:
                api_response.set_error_msg("Error calling project service: " + str(e))
                api_response.set_code(EAPIResponseCode.internal_error)
                return api_response.to_dict, api_response.code
            api_response.set_result(response.json())
            api_response.set_code(response.status_code)
            return api_response.to_dict, api_response.code
