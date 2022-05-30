from flask import request
from flask_jwt import jwt_required
from flask_restx import Resource
from common import ProjectClientSync

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
import httpx


api_ns_event = module_api.namespace('User Event', description='User events APIs', path='/v1')


class APIEvent(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_event.add_resource(self.Event, '/user/events')

    class Event(Resource):
        @jwt_required()
        def get(self):
            """ List user events """
            event_response = httpx.get(ConfigClass.AUTH_SERVICE + "events", params=request.args)
            event_response_json = event_response.json()
            events = event_response.json()["result"]
            project_codes = [i["detail"]["project_code"] for i in events if "project_code" in i["detail"]]

            # get projects by code, will be replace when project refactor is complete
            projects = []
            for code in project_codes:
                project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
                project = project_client.get(code=code)
                projects.append(project.json())

            for event in events:
                for project in projects:
                    if project["code"] == event["detail"].get("project_code"):
                        event["detail"]["project_name"] = project["name"]
            event_response_json["result"] = events
            return event_response_json, event_response.status_code
