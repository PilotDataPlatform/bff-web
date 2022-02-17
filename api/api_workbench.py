from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from flask import request
import requests
from models.api_response import APIResponse, EAPIResponseCode
from config import ConfigClass
from models.api_meta_class import MetaAPI
from api import module_api
from resources.validations import boolean_validate_role
from services.permissions_service.decorators import permissions_check

api_ns = module_api.namespace('Workbench', description='Workbench API', path='/v1')


class APIWorkbench(metaclass=MetaAPI):
    def api_registry(self):
        api_ns.add_resource(self.WorkbenchRestful, '/<project_geid>/workbench')

    class WorkbenchRestful(Resource):
        @jwt_required()
        @permissions_check("workbench", "*", "view")
        def get(self, project_geid):
            api_response = APIResponse()
            try:
                response = requests.get(ConfigClass.ENTITYINFO_SERVICE + f"{project_geid}/workbench")
            except Exception as e:
                api_response.set_error_msg("Error calling entityinfo: " + str(e))
                api_response.set_code(EAPIResponseCode.internal_error)
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

        @jwt_required()
        @permissions_check("workbench", "*", "create")
        def post(self, project_geid):
            api_response = APIResponse()
            data = request.get_json()
            payload = {
                **data,
                "deployed_by": current_identity["username"],
            }
            try:
                response = requests.post(ConfigClass.ENTITYINFO_SERVICE + f"{project_geid}/workbench", json=payload)
            except Exception as e:
                api_response.set_error_msg("Error calling entityinfo: " + str(e))
                api_response.set_code(EAPIResponseCode.internal_error)
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code

