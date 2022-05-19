from common import LoggerFactory, ProjectClientSync
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource

from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from services.permissions_service.decorators import permissions_check

logger = LoggerFactory('api_containers').get_logger()


class Containers(Resource):
    @jwt_required()
    def get(self):
        """
            List and Query on all projects"
        """
        logger.info("Calling Container get")
        payload = {
            "page": request.args.get("page"),
            "page_size": request.args.get("page_size"),
            "order_by": request.args.get("order_by"),
            "order_type": request.args.get("order_type"),
            "name": request.args.get("name"),
            "code": request.args.get("project_code"),
            "tags": request.args.get("tags"),
            "description": request.args.get("description"),
        }
        if current_identity["role"] != "admin":
            payload["discoverable"] = True

        result = {}
        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        result = project_client.search(payload)
        result["result"] = [i.json() for i in result["result"]]
        return result

        #if "create_time_start" in payload and "create_time_end" in payload:
        #    payload["create_time_start"] = datetime.datetime.utcfromtimestamp(int(payload["create_time_start"])).strftime('%Y-%m-%dT%H:%M:%S')
        #    payload["create_time_end"] = datetime.datetime.utcfromtimestamp(int(payload["create_time_end"])).strftime('%Y-%m-%dT%H:%M:%S')


class Container(Resource):
    @jwt_required()
    @permissions_check('project', '*', 'update')
    def put(self, project_code):
        '''
        Update a project
        '''
        logger.info("Calling Container put")
        api_response = APIResponse()
        update_data = request.get_json()
        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = project_client.get(code=project_code)
        result = project.update(**update_data)
        api_response.set_result(result.json())
        return api_response.to_dict, api_response.code
