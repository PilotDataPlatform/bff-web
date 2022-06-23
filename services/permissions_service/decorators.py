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
from fastapi import Request
from .utils import has_permission, get_project_code_from_request
from common import LoggerFactory
from services.dataset import get_dataset_by_id, get_dataset_by_code
from app.auth import get_current_identity
from models.api_response import EAPIResponseCode
from resources.error_handler import APIException

_logger = LoggerFactory('permissions').get_logger()


class PermissionsCheck:
    def __init__(self, resource, zone, operation):
        self.resource = resource
        self.zone = zone
        self.operation = operation

    async def __call__(self, request: Request):
        project_code = await get_project_code_from_request(request)
        if not project_code:
            _logger.error("Couldn't get project_code in permissions_check decorator")
        current_identity = get_current_identity(request)
        if has_permission(project_code, self.resource, self.zone, self.operation, current_identity):
            return True
        _logger.info(f"Permission denied for {project_code} - {self.resource} - {self.zone} - {self.operation}")
        raise APIException(error_msg="Permission Denied", status_code=EAPIResponseCode.forbidden.value)


class DatasetPermission:
    async def __call__(self, request: Request):
        dataset_id = await request.path_params.get("dataset_id")
        if not dataset_id:
            dataset_id = await request.json().get("dataset_id")
        dataset = get_dataset_by_id(dataset_id)
        current_identity = get_current_identity(request)
        if dataset["creator"] != current_identity["username"]:
            raise APIException(error_msg="Permission Denied", status_code=EAPIResponseCode.forbidden.value)
        return True


class DatasetPermissionByCode:
    async def __call__(self, request: Request):
        dataset_code = await request.path_params.get("dataset_code")
        if not dataset_code:
            dataset_code = await request.json().get("dataset_code")
        dataset = get_dataset_by_code(dataset_code)
        current_identity = get_current_identity(request)
        if dataset["creator"] != current_identity["username"]:
            raise APIException(error_msg="Permission Denied", status_code=EAPIResponseCode.forbidden.value)
        return True
