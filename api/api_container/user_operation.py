from datetime import datetime

import requests
from common import LoggerFactory, ProjectClientSync
from flask import request
from flask_jwt import jwt_required
from flask_restx import Resource

from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from resources.swagger_modules import permission_return, users_sample_return
from services.permissions_service.decorators import permissions_check

from .namespace import datasets_entity_ns, users_entity_ns

# init logger
_logger = LoggerFactory('api_user_ops').get_logger()


class Users(Resource):
    @users_entity_ns.response(200, users_sample_return)
    @jwt_required()
    @permissions_check('users', '*', 'view')
    def get(self):
        '''
        This method allow user to fetch all registered users in the platform.
        '''
        _logger.info('Call API for to admin fetching all users in the platform')
        api_response = APIResponse()
        try:
            data = {
                "username": request.args.get("name", None),
                "email": request.args.get("email", None),
                "order_by": request.args.get("order_by", None),
                "order_type": request.args.get("order_type", None),
                "page": request.args.get("page", 0),
                "page_size": request.args.get("page_size", 25),
                "status": request.args.get("status", None),
                "role": request.args.get("role", None),
            }
            # remove empty values
            data = {k: v for k, v in data.items() if v}
            response = requests.get(ConfigClass.AUTH_SERVICE + "users", params=data)
        except Exception as e:
            api_response.set_error_msg(f"Error get users from auth service: {str(e)}")
            api_response.set_code(EAPIResponseCode.internal_error)
            return api_response.to_dict, api_response.code
        return response.json(), response.status_code


class ContainerAdmins(Resource):
    @datasets_entity_ns.response(200, users_sample_return)
    @jwt_required()
    @permissions_check('project', '*', 'view')
    def get(self, project_geid):
        '''
        This method allow user to fetch all admins under a specific project with permissions.
        '''
        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE)
        project = project_client.get(project_geid)

        # fetch admins of the project
        payload = {
            "role_names": [f"{project.code}-admin"],
            "status": "active",
        }
        response = requests.post(ConfigClass.AUTH_SERVICE + "admin/roles/users", json=payload)
        return response.json(), response.status_code


class ContainerUsers(Resource):
    @datasets_entity_ns.response(200, users_sample_return)
    @jwt_required()
    @permissions_check('users', '*', 'view')
    def get(self, project_geid):
        '''
        This method allow user to fetch all users under a specific dataset with permissions.
        '''
        _logger.info('Calling API for fetching all users under dataset {}'.format(str(project_geid)))
        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = project_client.get(id=project_geid)

        # fetch admins of the project
        payload = {
            "role_names": [f"{project.code}-" + i for i in ["admin", "contributor", "collaborator"]],
            "status": "active",
        }
        response = requests.post(ConfigClass.AUTH_SERVICE + "admin/roles/users", json=payload)
        return response.json(), response.status_code


class UserContainerQuery(Resource):
    @users_entity_ns.response(200, permission_return)
    @jwt_required()
    def post(self, username):
        '''
        This method allow user to get the user's permission towards all containers (except default).
        '''
        _logger.info('Call API for fetching user {} role towards all projects'.format(username))
        data = request.get_json()

        payload = {
            "page": data.get("page", 0),
            "page_size": data.get("page_size", 25),
            "order_by": data.get("order_by", None),
            "order_type": data.get("order_type", None),
            "name": data.get("name"),
            "code": data.get("code"),
            "tags": data.get("tags"),
        }

        query = {
            "username": username,
            "exact": True,
        }
        response = requests.get(ConfigClass.AUTH_SERVICE + "admin/user", params=query)
        if response.status_code != 200:
            raise Exception(f"Error getting user {username} from auth service: " + str(response.json()))
        user_node = response.json()["result"]

        response = requests.get(ConfigClass.AUTH_SERVICE + "admin/users/realm-roles", params=query)
        if response.status_code != 200:
            raise Exception(f"Error getting realm roles for {username} from auth service: " + str(response.json()))
        realm_roles = response.json()["result"]
        realm_roles = [i["name"] for i in realm_roles]

        if data.get("is_all"):
            # This is terrible but it is required by frontend and will take to long for them to fix right now
            payload["page_size"] = 999

        if "create_time_start" in data and "create_time_end" in data:
            start_time = datetime.utcfromtimestamp(int(payload["query"]["create_time_start"]))
            end_time = datetime.utcfromtimestamp(int(payload["query"]["create_time_end"]))
            payload["create_time_start"] = start_time.strftime('%Y-%m-%dT%H:%M:%S')
            payload["create_time_end"] = end_time.strftime('%Y-%m-%dT%H:%M:%S')

        if user_node["role"] != "admin":
            roles = realm_roles
            project_codes = ",".join(list(set(i.split("-")[0] for i in roles)))
            payload["codes-any"] = project_codes

        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project_result = project_client.search(**payload)
        results = [i.json() for i in project_result["result"]]

        if user_node["role"] != "admin":
            for project in results:
                for role in realm_roles:
                    try:
                        role_project_code = role.split("-")[0]
                        project_role = role.split("-")[1]
                        if role_project_code == project["code"]:
                            project["permission"] = project_role
                            break
                    except Exception as e:
                        continue
        else:
            for project in results:
                project["permission"] = "admin"
        results["role"] = user_node["role"]
        return results, response.status_code


class ContainerUsersQuery(Resource):
    @jwt_required()
    @permissions_check('users', '*', 'view')
    def post(self, project_geid):
        _logger.info('Call API for fetching all users in a dataset')
        data = request.get_json()

        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = project_client.get(id=project_geid)

        # fetch admins of the project
        payload = {
            "role_names": [f"{project.code}-" + i for i in ["admin", "contributor", "collaborator"]],
            "status": "active",
            "username": data.get("username"),
            "email": data.get("email"),
            "page": data.get("page", 0),
            "page_size": data.get("page_size", 25),
            "order_by": data.get("order_by", "time_created"),
            "order_type": data.get("order_type", "desc"),
        }
        response = requests.post(ConfigClass.AUTH_SERVICE + "admin/roles/users", json=payload)
        return response.json(), response.status_code
