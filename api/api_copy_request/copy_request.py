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
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from services.permissions_service.decorators import PermissionsCheck
from services.permissions_service.utils import get_project_role

router = APIRouter(tags=["Copy Request"])


@cbv.cbv(router)
class CopyRequest:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/request/copy/{project_code}',
        summary="List copy requests by project_code",
        dependencies=[Depends(PermissionsCheck("copyrequest", "*", "view"))]
    )
    async def get(self, project_code: str, request: Request):
        api_response = APIResponse()
        data = request.query_params
        if get_project_role(project_code, self.current_identity) == "collaborator":
            data["submitted_by"] = self.current_identity["username"]

        try:
            response = requests.get(ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}", params=data)
        except Exception as e:
            api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.post(
        '/request/copy/{project_code}',
        summary="Create a copy request",
        dependencies=[Depends(PermissionsCheck("copyrequest", "*", "create"))]
    )
    async def post(self, project_code: str, request: Request):
        api_response = APIResponse()
        data = await request.json()

        if self.current_identity["role"] == "admin":
            # Platform admin can't create request
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_error_msg("Permission denied")
            return api_response.json_response()

        data["submitted_by"] = self.current_identity["username"]
        data["project_code"] = project_code
        try:
            response = requests.post(ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}", json=data)
        except Exception as e:
            api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.post(
        '/request/copy/{project_code}',
        summary="Create a copy request",
        dependencies=[Depends(PermissionsCheck("copyrequest", "*", "update"))]
    )
    async def put(self, project_code: str, request: Request):
        api_response = APIResponse()
        data = await request.json()
        put_data = data.copy()
        put_data["username"] = self.current_identity["username"]

        try:
            response = requests.put(ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}", json=put_data)
        except Exception as e:
            api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class CopyRequestFiles:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/request/copy/{project_code}/files',
        summary="View a copy requests files",
        dependencies=[Depends(PermissionsCheck("copyrequest", "*", "view"))]
    )
    async def get(self, project_code: str, request: Request):
        api_response = APIResponse()
        data = request.query_params.copy()

        try:
            response = requests.get(ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}/files", params=data)
        except Exception as e:
            api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.put(
        '/request/copy/{project_code}/files',
        summary="Update file status in a copy request",
        dependencies=[Depends(PermissionsCheck("copyrequest", "*", "update"))]
    )
    async def put(self, project_code: str, request: Request):
        api_response = APIResponse()
        data = await request.json()
        post_data = data.copy()
        post_data["username"] = self.current_identity["username"]

        try:
            response = requests.put(
                ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}/files",
                json=post_data,
                headers=request.headers
            )
        except Exception as e:
            api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.patch(
        '/request/copy/{project_code}/files',
        summary="Update file status in a copy request",
        dependencies=[Depends(PermissionsCheck("copyrequest", "*", "update"))]
    )
    async def patch(self, project_code: str, request: Request):
        api_response = APIResponse()
        data = await request.json()
        post_data = data.copy()
        post_data["username"] = self.current_identity["username"]

        try:
            response = requests.patch(
                ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}/files",
                json=post_data,
                headers=request.headers
            )
        except Exception as e:
            api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class CopyRequestPending:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/request/copy/{project_code}/pending-files',
        summary="Get pending files remaining in a copy request",
        dependencies=[Depends(PermissionsCheck("copyrequest", "*", "update"))]
    )
    def get(self, project_code: str, request: Request):
        api_response = APIResponse()
        try:
            response = requests.get(
                ConfigClass.APPROVAL_SERVICE + f"request/copy/{project_code}/pending-files",
                params=request.args,
            )
        except Exception as e:
            api_response.set_error_msg(f"Error calling request copy API: {str(e)}")
            return api_response.json_response()
        return JSONResponse(content=response.json(), status_code=response.status_code)
