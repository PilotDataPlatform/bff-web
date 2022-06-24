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
"""Folder creation API."""
import httpx
from common import LoggerFactory
from fastapi import APIRouter, Depends, Request
from fastapi_utils import cbv
from app.auth import jwt_required

from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from services.meta import search_entities
from services.permissions_service.decorators import PermissionsCheck

_logger = LoggerFactory('api_folder_creation').get_logger()

router = APIRouter(tags=["Folder Create"])


@cbv.cbv(router)
class FolderCreation:
    current_identity: dict = Depends(jwt_required)
    _logger = LoggerFactory('api_folder_creation').get_logger()

    @router.get(
        '/containers/{project_id}/folder',
        summary="List workbench entries",
        dependencies=[Depends(PermissionsCheck("file", "*", "upload"))]
    )
    async def post(self, project_id: str, request: Request):
        api_response = APIResponse()
        data = await request.json()
        folder_name = data.get("folder_name")
        project_code = data.get("project_code")
        zone = data.get("zone")
        zone = 0 if zone == "greenroom" else 1
        parent_path = data.get("parent_path")
        parent_entity = None
        entity_type = "folder"

        if not parent_path:
            # name folder
            entity_type = "name_folder"
        else:
            # ensure parent_path exists
            search_parent_path = ".".join(parent_path.split(".")[:-1])
            name = "".join(parent_path.split(".")[-1])
            parent_entity = search_entities(project_code, search_parent_path, zone, name=name)
            parent_entity = parent_entity[0]

        if len(folder_name) < 1 or len(folder_name) > 20:
            api_response.set_code(EAPIResponseCode.bad_request)
            api_response.set_error_msg("Folder should be 1 to 20 characters")
            return api_response.json_response()

        payload = {
            "name": folder_name,
            "zone": zone,
            "type": entity_type,
            "owner": self.current_identity["username"],
            "container_code": project_code,
            "container_type": "project",
            "size": 0,
            "location_uri": "",
            "version": "",
        }
        if parent_entity:
            payload["parent"] = parent_entity["id"]
            if parent_entity.get("parent_path"):
                payload["parent_path"] = parent_entity["parent_path"] + "." + parent_entity["name"]
            else:
                # name folder
                payload["parent_path"] = parent_entity["name"]

        with httpx.Client() as client:
            response = client.post(ConfigClass.METADATA_SERVICE + "item/", json=payload)
        return response.json(), response.status_code
