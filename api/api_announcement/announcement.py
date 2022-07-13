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
from common import ProjectClient
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=["Announcements"])


@cbv.cbv(router)
class AnnouncementRestful:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/announcements',
        summary="List announcements",
        dependencies=[Depends(PermissionsCheck("announcement", "*", "view"))]
    )
    async def get(self, request: Request):
        api_response = APIResponse()
        data = request.query_params
        if not data.get("project_code"):
            api_response.set_error_msg("Missing project code")
            api_response.set_code(EAPIResponseCode.bad_request)
            return api_response.json_response()

        response = requests.get(ConfigClass.NOTIFY_SERVICE + "announcements", params=data)
        if response.status_code != 200:
            api_response.set_error_msg(response.json())
            return api_response.json_response()
        api_response.set_result(response.json())
        return api_response.json_response()

    @router.post(
        '/announcements',
        summary="List announcements",
        dependencies=[Depends(PermissionsCheck("announcement", "*", "create"))]
    )
    async def post(self, request: Request):
        api_response = APIResponse()
        data = await request.json()
        if not data.get("project_code"):
            api_response.set_error_msg("Missing project code")
            api_response.set_code(EAPIResponseCode.bad_request)
            return api_response.json_response()

        project_client = ProjectClient(
            ConfigClass.PROJECT_SERVICE,
            ConfigClass.REDIS_URL
        )
        # will 404 if project doesn't exist
        await project_client.get(code=data["project_code"])

        data["publisher"] = self.current_identity["username"]
        response = requests.post(ConfigClass.NOTIFY_SERVICE + "announcements", json=data)
        if response.status_code != 200:
            api_response.set_error_msg(response.json()["error_msg"])
            response_dict = api_response.to_dict
            response_dict["code"] = response.status_code
            return JSONResponse(content=response_dict, status_code=response.status_code)
        api_response.set_result(response.json())
        return api_response.json_response()
