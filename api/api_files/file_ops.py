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
from common import LoggerFactory
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from config import ConfigClass
from models.api_response import EAPIResponseCode
from resources.error_handler import APIException
from services.meta import get_entity_by_id
from services.permissions_service.decorators import PermissionsCheck
from services.permissions_service.utils import get_project_role, has_permission

_logger = LoggerFactory('api_files_ops_v1').get_logger()

router = APIRouter(tags=["File Ops"])


# by default this proxy will ONLY call
# the Container related apis.
@cbv.cbv(router)
class FileActionTasks:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/files/actions/tasks',
        summary="Get task information",
        dependencies=[Depends(PermissionsCheck("tasks", "*", "view"))]
    )
    async def get(self, request: Request):
        data = request.query_params
        request_params = {**data}
        # here update the project_code to code
        request_params.update({"code": request_params.get("project_code")})
        url = ConfigClass.DATA_UTILITY_SERVICE + "tasks"
        response = requests.get(url, params=request_params)
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.delete(
        '/files/actions/tasks',
        summary="Delete tasks",
        dependencies=[Depends(PermissionsCheck("tasks", "*", "delete"))]
    )
    async def delete(self, request: Request):
        request_body = await request.json()
        url = ConfigClass.DATA_UTILITY_SERVICE + "tasks"
        response = requests.delete(url, json=request_body)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class FileActions:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/files/actions',
        summary="invoke an async file operation job",
    )
    async def post(self, request: Request):
        data_actions_utility_url = ConfigClass.DATA_UTILITY_SERVICE + "files/actions/"
        headers = request.headers
        request_body = await request.json()
        validate_request_params(request_body)
        operation = request_body.get("operation", None)
        project_code = request_body.get("project_code", None)
        targets = request_body["payload"]["targets"]
        # validate request
        session_id = headers.get("Session-Id", None)
        if not session_id:
            raise APIException(error_msg="Header Session-ID required", code=EAPIResponseCode.forbidden.value)

        if not has_permission(project_code, 'file', '*', operation.lower(), self.current_identity):
            raise APIException(error_msg="Permission denied", code=EAPIResponseCode.forbidden.value)

        if operation == 'delete':
            validate_delete_permissions(targets, project_code, self.current_identity)

        # request action utility API
        payload = request_body
        payload['session_id'] = session_id
        response = requests.post(data_actions_utility_url, json=payload, headers=request.headers)
        return JSONResponse(content=response.json(), status_code=response.status_code)


def validate_request_params(request_body: dict):
    if not request_body.get("payload"):
        raise APIException(error_msg="parameter 'payload' required", status_code=EAPIResponseCode.bad_request.value)

    targets = request_body["payload"].get("targets")
    if not targets:
        raise APIException(error_msg="targets required", status_code=EAPIResponseCode.bad_request.value)
    if type(targets) != list:
        raise APIException(error_msg="Invalid targets, must be an object list",
                           status_code=EAPIResponseCode.bad_request.value)
    if not request_body.get("operation"):
        raise APIException(error_msg="operation required", status_code=EAPIResponseCode.bad_request.value)
    if not request_body.get("project_code"):
        raise APIException(error_msg="project_code required", status_code=EAPIResponseCode.bad_request.value)


def validate_delete_permissions(targets: list, project_code, current_identity):
    '''
        Project admin can delete files
        Project collaborator can only delete the file belong to them
        Project contributor can only delete the greenroom file belong to them (confirm the file is greenroom file,
        and has owned by current user)
    '''
    user_project_role = get_project_role(project_code, current_identity)
    if user_project_role not in ["admin", "platform-admin"]:
        for target in targets:
            source = get_entity_by_id(target['id'])
            zone = "greenroom" if source["zone"] == 0 else "core"

            if user_project_role == 'contributor':
                root_folder = source["parent_path"].split("/")[0]
                if root_folder != current_identity['username']:
                    error_msg = "Permission denied on file: " + source['id']
                    raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.forbidden.value)
                if zone == "core":
                    error_msg = "Permission denied on file: " + source['id']
                    raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.forbidden.value)
            if user_project_role == 'collaborator':
                if zone == "greenroom":
                    root_folder = source["parent_path"].split(".")[0]
                    if root_folder != current_identity['username']:
                        error_msg = "Permission denied on file: " + source['id']
                        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.forbidden.value)
