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
import requests
from fastapi import Request
from common import LoggerFactory, ProjectClient
from config import ConfigClass

_logger = LoggerFactory('permissions').get_logger()


def has_permission(project_code, resource, zone, operation, current_identity):
    if current_identity["role"] == "admin":
        role = "platform_admin"
    else:
        if not project_code:
            _logger.info(
                "No project code and not a platform admin, permission denied")
            return False
        role = get_project_role(project_code, current_identity)
        if not role:
            _logger.info(
                "Unable to get project role in permissions check, user might not belong to project")
            return False

    try:
        payload = {
            "role": role,
            "resource": resource,
            "zone": zone,
            "operation": operation,
        }
        response = requests.get(
            ConfigClass.AUTH_SERVICE + "authorize", params=payload)
        if response.status_code != 200:
            raise Exception(f"Error calling authorize API - {response.json()}")
        if response.json()["result"].get("has_permission"):
            return True
        else:
            return False
    except Exception as e:
        error_msg = str(e)
        _logger.info(f"Exception on authorize call: {error_msg}")
        raise Exception(f"Error calling authorize API - {error_msg}")


def get_project_role(project_code, current_identity):
    role = None
    if current_identity["role"] == "admin":
        role = "platform_admin"
    else:
        possible_roles = [project_code + "-" + i for i in ["admin", "contributor", "collaborator"]]
        for realm_role in current_identity["realm_roles"]:
            # if this is a role for the correct project
            if realm_role in possible_roles:
                role = realm_role.replace(project_code + "-", "")
    return role


# NEED REDESIGN THIS FUNCTION
async def get_project_code_from_request(request: Request):
    if request.method == "POST":
        data = await request.json()

    elif request.method == "DELETE":
        data = await request.json()
        if not data:
            data = await request.json()
    else:
        data = request.query_params

    project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
    if "project_code" in data:
        return data["project_code"]
    if "project_geid" in data:
        project = await project_client.get(id=data["project_geid"])
        return project.code
    if "project_id" in data:
        project = await project_client.get(id=data["project_id"])
        return project.code
    kwargs = request.path_params
    if "project_code" in kwargs:
        return kwargs["project_code"]
    if "project_geid" in kwargs:
        project = await project_client.get(id=kwargs["project_geid"])
        return project.code
    if "project_id" in kwargs:
        project = await project_client.get(id=kwargs["project_id"])
        return project.code
