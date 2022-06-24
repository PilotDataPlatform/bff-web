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
from config import ConfigClass
from models.api_response import APIResponse
from common import LoggerFactory, ProjectClient
from services.permissions_service.decorators import PermissionsCheck
import requests
from fastapi import APIRouter, Depends, Request
from fastapi_utils import cbv
from app.auth import jwt_required


_logger = LoggerFactory('api_project').get_logger()

router = APIRouter(tags=["Project"])


@cbv.cbv(router)
class RestfulProject:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/project/{project_id}',
        summary="Get project by id",
        dependencies=[Depends(PermissionsCheck("project", "*", "view"))]
    )
    async def get(self, project_id: str):
        my_res = APIResponse()
        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = await project_client.get(id=project_id)
        my_res.set_result(project.json())
        return my_res.json_response()


@cbv.cbv(router)
class RestfulProjectByCode:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/project/code/{project_code}',
        summary="Get project by code",
        dependencies=[Depends(PermissionsCheck("project", "*", "view"))]
    )
    async def get(self, project_code: str):
        my_res = APIResponse()
        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = await project_client.get(code=project_code)
        my_res.set_result(project.json())
        return my_res.json_response()


@cbv.cbv(router)
class VirtualFolder:
    current_identity: dict = Depends(jwt_required)

    @router.put(
        '/project/{project_id}/collections',
        summary="Update project collections",
        dependencies=[Depends(PermissionsCheck("collections", "*", "update"))]
    )
    async def put(self, project_id: str, request: Request):
        url = ConfigClass.METADATA_SERVICE + "collection/"
        payload = await request.json()
        payload["owner"] = self.current_identity["username"]
        response = requests.put(url, json=payload)
        return response.json()
