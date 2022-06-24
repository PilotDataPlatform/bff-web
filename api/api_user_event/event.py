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
from common import ProjectClient

from config import ConfigClass
import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from app.auth import jwt_required


router = APIRouter(tags=["User Event"])


@cbv.cbv(router)
class Event:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/user/event',
        summary="List user events",
    )
    async def get(self, request: Request):
        """ List user events """
        event_response = httpx.get(ConfigClass.AUTH_SERVICE + "events", params=await request.query_params)
        event_response_json = event_response.json()
        events = event_response.json()["result"]
        project_codes = [i["detail"]["project_code"] for i in events if "project_code" in i["detail"]]

        # get projects by code, will be replace when project refactor is complete
        projects = []
        for code in project_codes:
            project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
            project = await project_client.get(code=code)
            projects.append(project.json())

        for event in events:
            for project in projects:
                if project["code"] == event["detail"].get("project_code"):
                    event["detail"]["project_name"] = project["name"]
        event_response_json["result"] = events
        return JSONResponse(content=event_response_json, status_code=event_response.status_code)
