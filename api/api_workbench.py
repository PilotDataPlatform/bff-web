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

router = APIRouter(tags=["Workbench"])


@cbv.cbv(router)
class WorkbenchRestful:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/{project_id}/workbench',
        summary="List workbench entries",
        dependencies=[Depends(PermissionsCheck("workbench", "*", "view"))]
    )
    async def get(self, project_id: str):
        api_response = APIResponse()
        payload = {
            "project_id": project_id,
        }
        try:
            response = requests.get(ConfigClass.PROJECT_SERVICE + "/v1/workbenches", params=payload)
        except Exception as e:
            api_response.set_error_msg("Error calling project: " + str(e))
            api_response.set_code(EAPIResponseCode.internal_error)
            return api_response.json_response()

        result = response.json()["result"]
        for resource in result:
            data = {
                "user_id": resource["deployed_by_user_id"],
            }
            response = requests.get(ConfigClass.AUTH_SERVICE + "admin/user", params=data)
            if response.status_code != 200:
                return JSONResponse(content=response.json(), status_code=response.status_code)
            resource["deploy_by_username"] = response.json()["result"]["username"]

        data = {i["resource"]: i for i in result}

        api_response.set_result(data)
        api_response.set_code(response.status_code)
        return api_response.json_response()

    @router.post(
        '/{project_id}/workbench',
        summary="create a workbench entry",
        dependencies=[Depends(PermissionsCheck("workbench", "*", "view"))]
    )
    async def post(self, project_id: str, request: Request):
        api_response = APIResponse()
        data = await request.json()
        payload = {
            "project_id": project_id,
            "resource": data.get("workbench_resource"),
            "deployed_by_user_id": self.current_identity["user_id"],
        }
        try:
            response = requests.post(ConfigClass.PROJECT_SERVICE + "/v1/workbenches", json=payload)
        except Exception as e:
            api_response.set_error_msg("Error calling project service: " + str(e))
            api_response.set_code(EAPIResponseCode.internal_error)
            return api_response.json_response()
        api_response.set_result(response.json())
        api_response.set_code(response.status_code)
        return api_response.json_response()
