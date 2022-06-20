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
from config import ConfigClass
from models.api_response import APIResponse
from models.api_meta_class import MetaAPI
from common import LoggerFactory, ProjectClientSync
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
            project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
            project = project_client.get(id=project_geid)
            my_res.set_result(project.json())
            return my_res.to_dict, my_res.code

    class RestfulProjectByCode(Resource):
        def get(self, project_code):
            my_res = APIResponse()
            project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
            project = project_client.get(code=project_code)
            my_res.set_result(project.json())
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
