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
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource
from common import LoggerFactory

from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from resources.error_handler import APIException
from services.permissions_service.utils import get_project_role, has_permission


_logger = LoggerFactory('api_meta').get_logger()


class FileDetailBulk(Resource):
    @jwt_required()
    def post(self):
        api_response = APIResponse()
        payload = {
            "ids": request.get_json().get("ids", [])
        }
        response = requests.get(ConfigClass.METADATA_SERVICE + "items/batch", params=payload)
        if response.status_code != 200:
            return response.json(), response.status_code
        file_node = response.json()["result"]

        for file_node in response.json()["result"]:
            if file_node["zone"] == 0:
                zone = "greenroom"
            else:
                zone = "core"
            if not has_permission(file_node["container_code"], "file", zone, "view"):
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_error_msg("Permission Denied")
                return api_response.to_dict, api_response.code
        result = response.json()
        for entity in result["result"]:
            entity["zone"] = "greenroom" if entity["zone"] == 0 else "core"
        return result, response.status_code


class FileMeta(Resource):
    @jwt_required()
    def get(self):
        """
            Proxy for entity info file META API, handles permission checks
        """
        api_response = APIResponse()
        _logger.info('Call API for fetching file info')
        page_size = int(request.args.get('page_size', 25))
        page = int(request.args.get('page', 0))
        order_by = request.args.get('order_by', 'created_time')
        order_type = request.args.get('order_type', 'desc')
        zone = request.args.get('zone', '')
        project_code = request.args.get('project_code', '')
        parent_path = request.args.get('parent_path', '')
        source_type = request.args.get('source_type', '')

        name = request.args.get('name', '')
        owner = request.args.get('owner', '')
        archived = request.args.get('archived', False, type=lambda v: v.lower() == 'true')

        if source_type not in ["trash", "project", "folder", "collection"]:
            _logger.error('Invalid zone')
            api_response.set_code(EAPIResponseCode.bad_request)
            api_response.set_error_msg('Invalid zone')
            return api_response.to_dict, api_response.code

        if zone not in ["greenroom", "core", 'all']:
            _logger.error('Invalid zone')
            api_response.set_code(EAPIResponseCode.bad_request)
            api_response.set_error_msg('Invalid zone')
            return api_response.to_dict, api_response.code

        payload = {
            "page": page,
            "page_size": page_size,
            "order": order_type,
            "sorting": order_by,
            "zone": 0 if zone == "greenroom" else 1,
            "container_code": project_code,
            "recursive": False,
        }
        if name:
            payload["name"] = name.replace("%", "\%") + "%",
        if owner:
            payload["owner"] = owner.replace("%", "\%") + "%",
        payload["archived"] = archived

        project_role = get_project_role(project_code)

        if source_type == "folder":
            payload["parent_path"] = parent_path
        elif source_type == "trash":
            payload["parent_path"] = current_identity["username"]
        elif source_type == "project":
            payload["parent_path"] = None
        elif source_type == "collection":
            collection_id = request.args.get("parent_id")
            if not collection_id:
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_error_msg('parent_id required for collection')
                return api_response.to_dict, api_response.code
            payload["id"] = collection_id

        if project_role in ["contributor", "collaborator"]:
            if not (project_role == "collaborator" and zone == "core"):
                if source_type == "folder":
                    if current_identity["username"] != parent_path.split(".")[0]:
                        _logger.error('Permission Denied')
                        api_response.set_code(EAPIResponseCode.forbidden)
                        api_response.set_error_msg('Permission Denied')
                        return api_response.to_dict, api_response.code

        if not has_permission(project_code, "file", zone.lower(), "view"):
            username = current_identity["username"]
            _logger.info(f"Permissions denied for user {username} in meta listing")
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_error_msg("Permission Denied")
            return api_response.to_dict, api_response.code

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
        return result, response.status_code
