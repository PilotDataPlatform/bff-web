from common import LoggerFactory, ProjectClientSync
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource

from config import ConfigClass
from models.api_response import APIResponse
from services.permissions_service.decorators import permissions_check

logger = LoggerFactory('api_containers').get_logger()


class Containers(Resource):
    @jwt_required()
    def get(self):
        """
            List and Query on all projects"
        """
        logger.info("Calling Container get")
        api_response = APIResponse()

        name = None
        if request.args.get("name"):
            name = "%" + request.args.get("name") + "%"
        code = None
        if request.args.get("code"):
            code = "%" + request.args.get("code") + "%"

        description = None
        if request.args.get("description"):
            description = "%" + request.args.get("description") + "%"

        tags = request.args.get('tags')
        if tags:
            tags = tags.split(",")

        payload = {
            "page": request.args.get("page"),
            "page_size": request.args.get("page_size"),
            "order_by": request.args.get("order_by"),
            "order_type": request.args.get("order_type"),
            "name": name,
            "code": code,
            "tags_all": tags,
            "description": description,
        }
        if current_identity["role"] != "admin":
            payload["is_discoverable"] = True

        if "create_time_start" in request.args and "create_time_end" in request.args:
            payload["created_at_start"] = request.args.get("create_time_start")
            payload["created_at_end"] = request.args.get("create_time_end")

        result = {}
        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        result = project_client.search(**payload)
        api_response.set_result([i.json() for i in result["result"]])
        api_response.set_total(result["total"])
        api_response.set_num_of_pages(result["num_of_pages"])
        return api_response.to_dict, api_response.code


class Container(Resource):
    @jwt_required()
    @permissions_check('project', '*', 'update')
    def put(self, project_id):
        '''
        Update a project
        '''
        logger.info("Calling Container put")
        api_response = APIResponse()
        update_data = request.get_json()
        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = project_client.get(id=project_id)

        if "icon" in update_data:
            logo = update_data["icon"]
            project.upload_logo(logo)
            del update_data["icon"]

        result = project.update(**update_data)
        api_response.set_result(result.json())
        return api_response.to_dict, api_response.code
