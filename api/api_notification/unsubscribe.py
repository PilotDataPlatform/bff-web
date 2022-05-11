from flask_restx import Resource
from flask_jwt import jwt_required
from models.api_meta_class import MetaAPI
from flask import request
from models.api_response import APIResponse
from api import module_api
from config import ConfigClass
from services.permissions_service.decorators import permissions_check
import requests

api_resource = module_api.namespace(
    'Notification', description='Notification API', path='/v1')


class APIUnsubscribe(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(
            self.UnsubscribeRestful, '/unsubscribe')

    class UnsubscribeRestful(Resource):
        @jwt_required()
        def post(self):
            api_response = APIResponse()
            body = request.get_json()
            response = requests.post(ConfigClass.NOTIFY_SERVICE+'/v1/unsubscribe', json=body)
            if response.status_code != 200:
                api_response.set_error_msg(response.json())
                return api_response.to_dict, response.status_code
            api_response.set_result(response.json())
            return api_response.to_dict, api_response.code
