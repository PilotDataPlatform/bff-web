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
from models.api_response import APIResponse, EAPIResponseCode
from resources.error_handler import APIException
from services.permissions_service.utils import get_project_role, has_permission

_logger = LoggerFactory('api_meta').get_logger()

router = APIRouter(tags=["File Meta"])


@cbv.cbv(router)
class FileDetailBulk:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/files/bulk/detail',
        summary="Bulk get files from list of ids",
    )
    async def post(self, request: Request):
        api_response = APIResponse()
        data = await request.json()
        payload = {
            "ids": data.get("ids", [])
        }
        response = requests.get(ConfigClass.METADATA_SERVICE + "items/batch", params=payload)
        if response.status_code != 200:
            return JSONResponse(content=response.json(), status_code=response.status_code)
        file_node = response.json()["result"]

        for file_node in response.json()["result"]:
            if file_node["zone"] == 0:
                zone = "greenroom"
            else:
                zone = "core"
            if not has_permission(file_node["container_code"], "file", zone, "view", self.current_identity):
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_error_msg("Permission Denied")
                return api_response.json_response()
        result = response.json()
        for entity in result["result"]:
            entity["zone"] = "greenroom" if entity["zone"] == 0 else "core"
        return JSONResponse(content=result, status_code=response.status_code)


@cbv.cbv(router)
class FileMeta:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/files/meta',
        summary="List files in project or folder",
    )
    async def get(self, request: Request):
        """
            Proxy for entity info file META API, handles permission checks
        """
        api_response = APIResponse()
        _logger.info('Call API for fetching file info')
        page_size = int(request.query_params.get('page_size', 25))
        page = int(request.query_params.get('page', 0))
        order_by = request.query_params.get('order_by', 'created_time')
        order_type = request.query_params.get('order_type', 'desc')
        zone = request.query_params.get('zone', '')
        project_code = request.query_params.get('project_code', '')
        parent_path = request.query_params.get('parent_path', '')
        source_type = request.query_params.get('source_type', '')

        name = request.query_params.get('name', '')
        owner = request.query_params.get('owner', '')
        archived = request.query_params.get('archived', False)

        if source_type not in ["trash", "project", "folder", "collection"]:
            _logger.error('Invalid zone')
            api_response.set_code(EAPIResponseCode.bad_request)
            api_response.set_error_msg('Invalid zone')
            return api_response.json_response()

        if zone not in ["greenroom", "core", 'all']:
            _logger.error('Invalid zone')
            api_response.set_code(EAPIResponseCode.bad_request)
            api_response.set_error_msg('Invalid zone')
            return api_response.json_response()

        if zone == "greenroom":
            zone_num = 0
        elif zone == "core":
            zone_num = 1
        else:
            zone_num = None

        payload = {
            "page": page,
            "page_size": page_size,
            "order": order_type,
            "sorting": order_by,
            "zone": zone_num,
            "container_code": project_code,
            "recursive": False,
        }
        if name:
            payload["name"] = name.replace("%", "\%") + "%",
        if owner:
            payload["owner"] = owner.replace("%", "\%") + "%",
        payload["archived"] = archived

        project_role = get_project_role(project_code, self.current_identity)

        if source_type == "folder":
            payload["parent_path"] = parent_path
        elif source_type == "trash":
            payload["parent_path"] = self.current_identity["username"]
        elif source_type == "project":
            payload["parent_path"] = None
        elif source_type == "collection":
            collection_id = request.query_params.get("parent_id")
            if not collection_id:
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_error_msg('parent_id required for collection')
                return api_response.json_response()
            payload["id"] = collection_id

        if project_role in ["contributor", "collaborator"]:
            if not (project_role == "collaborator" and zone == "core"):
                if source_type == "folder":
                    if self.current_identity["username"] != parent_path.split(".")[0]:
                        _logger.error('Permission Denied')
                        api_response.set_code(EAPIResponseCode.forbidden)
                        api_response.set_error_msg('Permission Denied')
                        return api_response.json_response()

        if zone == "all":
            zone = "*"
        if not has_permission(project_code, "file", zone.lower(), "view", self.current_identity):
            username = self.current_identity["username"]
            _logger.info(f"Permissions denied for user {username} in meta listing")
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_error_msg("Permission Denied")
            return api_response.json_response()

        if source_type == 'collection':
            url = ConfigClass.METADATA_SERVICE + 'collection/items'
        else:
            url = ConfigClass.METADATA_SERVICE + 'items/search'
        response = requests.get(url, params=payload)
        if response.status_code != 200:
            error_msg = f'Error calling Meta service get_node_by_id: {response.json()}'
            raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
        result = response.json()
        for entity in result["result"]:
            entity["zone"] = "greenroom" if entity["zone"] == 0 else "core"
        return JSONResponse(content=result, status_code=response.status_code)
