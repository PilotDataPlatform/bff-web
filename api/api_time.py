from flask_restx import Api, Resource, fields
from flask_jwt import jwt_required, current_identity
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from models.api_meta_class import MetaAPI
from resources.swagger_modules import create_invitation_request_model, create_invitation_return_example
from resources.swagger_modules import read_invitation_return_example
from services.logger_services.logger_factory_service import SrvLoggerFactory
from api import module_api
from flask import request
import json
import requests
import datetime

api_ns_time = module_api.namespace(
    'Time Restful', description='Portal Time Restful', path='/v1')

timestamp_get_response_example = '''
    {
        "code": 200,
        "error_msg": "",
        "page": 1,
        "total": 1,
        "num_of_pages": 1,
        "result": {
            "timestamp": 1605811211.763606
        }
    }
    '''

class APITimestamp(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_time.add_resource(self.Restful, '/timestamp') ## for browser
    class Restful(Resource):
        ## init logger
        _logger = SrvLoggerFactory('api_time').get_logger()
        @api_ns_time.response(200, timestamp_get_response_example)
        def get(self):
            '''
            Get standard timestamp
            '''
            self._logger.info("Get Request Gotten")
            ## init response
            my_res = APIResponse()
            ## access content from timestamp manager service
            my_res.set_code(EAPIResponseCode.success)
            my_res.set_result({
                "timestamp": datetime.datetime.utcnow().timestamp()
            })
            return my_res.to_dict, my_res.code
