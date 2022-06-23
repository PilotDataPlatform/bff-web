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
from common import LoggerFactory, ProjectClientSync
from fastapi import APIRouter, Depends, Request
from fastapi_utils import cbv
from app.auth import jwt_required

from config import ConfigClass
from models.api_response import APIResponse

logger = LoggerFactory('api_containers').get_logger()

router = APIRouter(tags=["Containers"])


@cbv.cbv(router)
class Containers:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/containers',
        summary="List and query all projects",
    )
    async def get(self, request: Request):
        """
            List and Query on all projects"
        """
        logger.info("Calling Container get")
        api_response = APIResponse()

        name = None
        if await request.query_params.get("name"):
            name = "%" + await request.query_params.get("name") + "%"
        code = None
        if await request.query_params.get("code"):
            code = "%" + await request.query_params.get("code") + "%"

        description = None
        if await request.query_params.get("description"):
            description = "%" + await request.query_params.get("description") + "%"

        tags = request.query_params.get('tags')
        if tags:
            tags = tags.split(",")

        payload = {
            "page": await request.query_params.get("page"),
            "page_size": await request.query_params.get("page_size"),
            "order_by": await request.query_params.get("order_by"),
            "order_type": await request.query_params.get("order_type"),
            "name": name,
            "code": code,
            "tags_all": tags,
            "description": description,
        }
        if self.current_identity["role"] != "admin":
            payload["is_discoverable"] = True

        if "create_time_start" in await request.query_params and "create_time_end" in await request.query_params:
            payload["created_at_start"] = await request.query_params.get("create_time_start")
            payload["created_at_end"] = await request.query_params.get("create_time_end")

        result = {}
        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        result = project_client.search(**payload)
        api_response.set_result([i.json() for i in result["result"]])
        api_response.set_total(result["total"])
        api_response.set_num_of_pages(result["num_of_pages"])
        return api_response.to_dict, api_response.code


@cbv.cbv(router)
class Container:
    current_identity: dict = Depends(jwt_required)

    @router.put(
        '/containers/{project_id}',
        summary="Update a project",
    )
    async def put(self, project_id: str, request: Request):
        '''
        Update a project
        '''
        logger.info("Calling Container put")
        api_response = APIResponse()
        update_data = await request.json()
        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = project_client.get(id=project_id)

        if "icon" in update_data:
            logo = update_data["icon"]
            project.upload_logo(logo)
            del update_data["icon"]

        result = project.update(**update_data)
        api_response.set_result(result.json())
        return api_response.to_dict, api_response.code
