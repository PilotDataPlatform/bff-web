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
from fastapi import APIRouter, Depends, Request
from fastapi_utils import cbv
from app.auth import jwt_required

from services.permissions_service.utils import has_permission, get_project_role
from common import LoggerFactory
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
import requests

router = APIRouter(tags=["Archive"])

_logger = LoggerFactory('api_archive').get_logger()


@cbv.cbv(router)
class Archive:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/archive',
        summary="Get a zip preview given file id",
    )
    def get(self, file_id: str):
        _logger.info("GET archive called in bff")
        api_response = APIResponse()

        # Retrieve file info from metadata service
        request = requests.get(f"{ConfigClass.METADATA_SERVICE}item/{file_id}")
        file_response = request.json()["result"]
        if not file_response:
            _logger.error(f"File not found with following id: {file_id}")
            api_response.set_code(EAPIResponseCode.not_found)
            api_response.set_result("File not found")
            return api_response.to_dict, api_response.code

        if file_response["zone"] == 0:
            zone = 'greenroom'
        else:
            zone = 'core'

        project_code = file_response["container_code"]
        if not has_permission(project_code, 'file', zone, 'view'):
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_result("Permission Denied")
            return api_response.to_dict, api_response.code

        if not self.has_file_permissions(project_code, file_response):
            api_response.set_code(EAPIResponseCode.forbidden)
            api_response.set_result("Permission Denied")
            return api_response.to_dict, api_response.code

        try:
            response = requests.get(ConfigClass.DATA_UTILITY_SERVICE + "archive", params={"file_id": file_id})
        except Exception as e:
            _logger.info(f"Error calling dataops gr: {str(e)}")
            return response.json(), response.status_code
        return response.json(), response.status_code

    def has_file_permissions(self, project_code, file_info):
        if self.current_identity["role"] != "admin":
            role = get_project_role(project_code)
            if role != "admin":
                root_folder = file_info["parent_path"].split(".")[0]
                if role == "contributor":
                    # contrib must own the file to attach manifests
                    if root_folder != self.current_identity["username"]:
                        return False
                elif role == "collaborator":
                    if file_info["zone"] == 0:
                        if root_folder != self.current_identity["username"]:
                            return False
        return True
