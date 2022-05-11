import requests
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from models.api_meta_class import MetaAPI
from flask import request
from models.api_response import APIResponse
from api import module_api
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode

api_resource = module_api.namespace(
    'Notification', description='Notification API', path='/v1')


class APINotification(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(
            self.NotificationRestful, '/notification')

    class NotificationRestful(Resource):
        @jwt_required()
        def get(self):
            api_response = APIResponse()
            params = request.args
            response = requests.get(ConfigClass.NOTIFY_SERVICE+'/v1/notification', params=params)
            if response.status_code != 200:
                api_response.set_error_msg(response.json())
                return api_response.to_dict, response.status_code
            api_response.set_result(response.json())
            return api_response.to_dict, api_response.code

        @jwt_required()
        def post(self):
            api_response = APIResponse()
            if current_identity["role"] != "admin":
                api_response.set_error_msg("Permission denied")
                api_response.set_code(EAPIResponseCode.forbidden)
                return api_response.to_dict, api_response.code
            body = request.get_json()
            response = requests.post(ConfigClass.NOTIFY_SERVICE+'/v1/notification', json=body)
            if response.status_code != 200:
                api_response.set_error_msg(response.json())
                return api_response.to_dict, response.status_code
            api_response.set_result(response.json())
            return api_response.to_dict, api_response.code

        @jwt_required()
        def put(self):
            api_response = APIResponse()
            if current_identity["role"] != "admin":
                api_response.set_error_msg("Permission denied")
                api_response.set_code(EAPIResponseCode.forbidden)
                return api_response.to_dict, api_response.code
            params = request.args
            body = request.get_json()
            response = requests.put(ConfigClass.NOTIFY_SERVICE+'/v1/notification', params=params, json=body)
            if response.status_code != 200:
                api_response.set_error_msg(response.json())
                return api_response.to_dict, response.status_code
            api_response.set_result(response.json())
            return api_response.to_dict, api_response.code
        
        @jwt_required()
        def delete(self):
            api_response = APIResponse()
            if current_identity["role"] != "admin":
                api_response.set_error_msg("Permission denied")
                api_response.set_code(EAPIResponseCode.forbidden)
                return api_response.to_dict, api_response.code
            params = request.args
            response = requests.delete(ConfigClass.NOTIFY_SERVICE+'/v1/notification', params=params)
            if response.status_code != 200:
                api_response.set_error_msg(response.json())
                return api_response.to_dict, response.status_code
            api_response.set_result(response.json())
            return api_response.to_dict, api_response.code


class APINotifications(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(
            self.NotificationsRestful, '/notifications')

    class NotificationsRestful(Resource):
        @jwt_required()
        def get(self):
            api_response = APIResponse()
            params = request.args
            response = requests.get(ConfigClass.NOTIFY_SERVICE+'/v1/notifications', params=params)
            if response.status_code != 200:
                api_response.set_error_msg(response.json())
                return api_response.to_dict, response.status_code
            api_response.set_result(response.json())
            return api_response.to_dict, api_response.code
