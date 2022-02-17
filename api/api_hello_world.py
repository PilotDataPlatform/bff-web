from flask_restx import Api, Resource, fields
from flask import request, Response, redirect
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from models.api_meta_class import MetaAPI
from api import module_api
from services.helloworld_services.helloworld_manager import SrvHelloWolrd
from services.logger_services.logger_factory_service import SrvLoggerFactory
from resources.swagger_modules import hello_indoc_return_example
import time
import multiprocessing

api_ns_hello = module_api.namespace('Hello World', description='For backend services down/on testing', path ='/v1')

## for backend services down/on testing
class APIHelloWorld(metaclass=MetaAPI):
    def api_registry(self):
        # api_ns_hello.add_resource(self.Restful, '/helloworld/test_gua') ## for browser
        api_ns_hello.add_resource(self.Restful, '/helloworld') ## for curl/postman
    class Restful(Resource):
        ## init logger
        _logger = SrvLoggerFactory('api_hello_world').get_logger()
        @api_ns_hello.response(200, hello_indoc_return_example)
        def get(self):
            '''
            Check service environment and status
            '''
            self._logger.info("Get Request Gotten")
            ## init response
            my_res = APIResponse()
            ## access content from helloworld manager service
            my_srv = SrvHelloWolrd()
            hello_content = my_srv.get_content()
            my_res.set_code(EAPIResponseCode.success)
            my_res.set_result("Serivce on, CenterUrl: {},  Env: {}".format(ConfigClass.CONFIG_CENTER, ConfigClass.env))
            return my_res.to_dict
        def post(self):
            '''
            Hello Wolrd PlaceHolder
            '''
            self._logger.info("Post Request Gotten")
            time.sleep(3)
            ## show form data
            my_form = request.form
            my_form_dict = my_form.to_dict()
            my_form_dict['cpu'] = multiprocessing.cpu_count()
            self._logger.info(str(my_form_dict))
            ## init response
            my_res = APIResponse()
            my_res.set_code(EAPIResponseCode.success)
            my_res.set_result(my_form_dict)
            return my_res.to_dict, my_res.code
