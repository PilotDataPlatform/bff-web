from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from models.api_meta_class import MetaAPI
from common import LoggerFactory
from services.container_services.container_manager import SrvContainerManager
from services.permissions_service.decorators import permissions_check
from api import module_api
from flask import request
import requests

api_ns_projects = module_api.namespace('Project Restful', description='For project feature', path='/v1')
api_ns_project = module_api.namespace('Project Restful', description='For project feature', path='/v1')

_logger = LoggerFactory('api_project').get_logger()


class APIProject(metaclass=MetaAPI):
    '''
    [POST]/projects
    [GET]/projects
    [GET]/project/<project_id>
    '''

    def api_registry(self):
        api_ns_project.add_resource(
            self.RestfulProject, '/project/<project_geid>')
        api_ns_project.add_resource(
            self.RestfulProjectByCode, '/project/code/<project_code>')
        api_ns_project.add_resource(
            self.VirtualFolder, '/project/<project_geid>/collections')

    class RestfulProject(Resource):
        @jwt_required()
        @permissions_check('project', '*', 'view')
        def get(self, project_geid):
            # init resp
            my_res = APIResponse()
            # init container_mgr
            container_mgr = SrvContainerManager()
            if not project_geid:
                my_res.set_code(EAPIResponseCode.bad_request)
                my_res.set_error_msg('Invalid request, need project_geid')

            project_info = container_mgr.get_by_project_geid(project_geid)
            if project_info[0]:
                if len(project_info[1]) > 0:
                    my_res.set_code(EAPIResponseCode.success)
                    my_res.set_result(project_info[1][0])
                else:
                    my_res.set_code(EAPIResponseCode.not_found)
                    my_res.set_error_msg('Project Not Found: ' + project_geid)
            else:
                my_res.set_code(EAPIResponseCode.internal_error)
            return my_res.to_dict, my_res.code

    class RestfulProjectByCode(Resource):
        def get(self, project_code):
            # init resp
            my_res = APIResponse()
            # init container_mgr
            container_mgr = SrvContainerManager()
            if not project_code:
                my_res.set_code(EAPIResponseCode.bad_request)
                my_res.set_error_msg('Invalid request, need project_code')
            project_info = container_mgr.get_by_project_code(project_code)
            if project_info[0]:
                if len(project_info[1]) > 0:
                    my_res.set_code(EAPIResponseCode.success)
                    my_res.set_result(project_info[1][0])
                else:
                    my_res.set_code(EAPIResponseCode.not_found)
                    my_res.set_error_msg('Project Not Found: ' + project_code)
            else:
                my_res.set_code(EAPIResponseCode.internal_error)
            return my_res.to_dict, my_res.code

    class VirtualFolder(Resource):
        @jwt_required()
        @permissions_check('collections', '*', 'update')
        def put(self, project_geid):
            url = ConfigClass.METADATA_SERVICE + "collection/"
            payload = request.get_json()
            payload["owner"] = current_identity["username"]
            response = requests.put(url, json=payload)
            return response.json()