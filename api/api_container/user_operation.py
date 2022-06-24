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
import math
from datetime import datetime

import requests
from common import LoggerFactory, ProjectClientSync
from fastapi import APIRouter, Depends, Request
from fastapi_utils import cbv
from app.auth import jwt_required

from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from services.permissions_service.decorators import PermissionsCheck


# init logger
_logger = LoggerFactory('api_user_ops').get_logger()

router = APIRouter(tags=["User Operations"])


@cbv.cbv(router)
class Users:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/users/platform',
        summary="List all users in platform",
        dependencies=[Depends(PermissionsCheck("users", "*", "view"))]
    )
    def get(self, request: Request):
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
            return api_response.json_response()
        return response.json(), response.status_code


@cbv.cbv(router)
class ContainerAdmins:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/containers/{project_id}/admins"',
        summary="List all admins in a project",
        dependencies=[Depends(PermissionsCheck("project", "*", "view"))]
    )
    async def get(self, project_id: str):
        '''
        This method allow user to fetch all admins under a specific project with permissions.
        '''
        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = project_client.get(project_id)

        # fetch admins of the project
        payload = {
            "role_names": [f"{project.code}-admin"],
            "status": "active",
        }
        response = requests.post(ConfigClass.AUTH_SERVICE + "admin/roles/users", json=payload)
        return response.json(), response.status_code


class ContainerUsers:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/containers/{project_id}/users',
        summary="List all users in a project",
        dependencies=[Depends(PermissionsCheck("users", "*", "view"))]
    )
    def get(self, project_id: str, request: Request):
        '''
        This method allow user to fetch all users under a specific dataset with permissions.
        '''
        data = request.query_params
        _logger.info('Calling API for fetching all users under dataset {}'.format(str(project_id)))
        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = project_client.get(id=project_id)

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


class UserContainerQuery:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/users/{username}/containers"',
        summary="Query user's containers",
        dependencies=[Depends(PermissionsCheck("users", "*", "view"))]
    )
    async def post(self, username: str, request: Request):
        '''
        This method allow user to get the user's permission towards all containers (except default).
        '''
        _logger.info('Call API for fetching user {} role towards all projects'.format(username))
        data = await request.json()

        name = None
        if data.get("name"):
            name = "%" + data.get("name") + "%"
        code = None
        if data.get("code"):
            code = "%" + data.get("code") + "%"

        description = None
        if data.get("description"):
            description = "%" + data.get("description") + "%"

        payload = {
            "page": data.get("page", 0),
            "page_size": data.get("page_size", 25),
            "order_by": data.get("order_by", None),
            "order_type": data.get("order_type", None),
            "name": name,
            "code": code,
            "tags_all": data.get("tags"),
            "description": description,
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
        realm_roles = {}
        for role in response.json()["result"]:
            try:
                realm_roles[role["name"].split("-")[0]] = role["name"].split("-")[1]
            except Exception:
                continue

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
            payload["code_any"] = project_codes

        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project_result = project_client.search(**payload)
        projects = [i.json() for i in project_result["result"]]

        if user_node["role"] != "admin":
            for project in projects:
                project["permission"] = realm_roles.get(project["code"])
        else:
            for project in projects:
                project["permission"] = "admin"
        results = {
            "results": projects,
            "role": user_node["role"],
            "total": project_result["total"],
            "page": project_result["page"],
            "num_of_pages": int(math.ceil(project_result["total"] / payload["page_size"])),
        }
        return results, EAPIResponseCode.success.value
