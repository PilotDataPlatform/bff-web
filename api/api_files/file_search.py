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

from typing import Any
from typing import Dict

import httpx
from common import LoggerFactory
from common import ProjectClient
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi_utils import cbv
from starlette.datastructures import MultiDict

from app.auth import jwt_required
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.permissions_service.utils import get_project_role

_logger = LoggerFactory('api_files_ops_v4').get_logger()

router = APIRouter(tags=['File Search'])


def get_zone_label(zone: int) -> str:
    """Get zone label for zone number."""

    try:
        return ConfigClass.ZONE_LABEL_MAPPING[zone]
    except KeyError:
        return str(zone)


def replace_zone_labels(response: Dict[str, Any]) -> Dict[str, Any]:
    """Replace zone numbers with string values."""

    total_per_zone = response['total_per_zone']
    zones = list(total_per_zone.keys())
    for zone in zones:
        new_key = get_zone_label(int(zone))
        total_per_zone[new_key] = total_per_zone.pop(zone)

    result = response['result']
    for item in result:
        item['zone'] = get_zone_label(item['zone'])

    return response


@cbv.cbv(router)
class FileSearch:
    current_identity: dict = Depends(jwt_required)

    @router.get('/{project_code}/files/search', summary='Search files using search service')
    async def get(self, project_code: str, request: Request):
        """Fetch file info from search service."""

        _res = APIResponse()

        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = await project_client.get(code=project_code)
        project_code = project.code

        if self.current_identity['role'] != 'admin':
            project_role = get_project_role(project_code, self.current_identity)

            _res.set_code(EAPIResponseCode.forbidden)
            _res.set_error_msg('Not implemented.')
            return _res.json_response()

            # TODO: Revise this in connection with search service
            if project_role == 'contributor':
                # Make sure contributor is restrict to querying there own files/folders
                # the reason use display_path is all own files/folders under user's name folder
                if 'display_path' not in query:
                    _logger.error('Non-admin user does not have access to query all user file info')
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_error_msg(
                        'Permission Denied, Non-admin user does not have access to query all user file info'
                    )
                    return _res.json_response()
                elif self.current_identity['username'] not in query['display_path']['value']:
                    _logger.error('Non-admin user can only have access to their own file info')
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_error_msg('Permission Denied, Non-admin user can only have access to their own file info')
                    return _res.json_response()
                elif 'zone' not in query:
                    _logger.error('Zone and file_type is required if user role is contributor')
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_error_msg('Permission Denied, zone and file_type is required if user role is contributor')
                    return _res.json_response()
                elif query['zone']['value'] == 'core':
                    _logger.error('Contributor cannot fetch core files or processed files')
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_error_msg('Permission Denied, contributor cannot fetch core files or processed files')
                    return _res.json_response()
            elif project_role == 'collaborator':
                display_path = query['display_path']['value']
                if query['zone']['value'] == 'greenroom' and 'display_path' not in query:
                    _logger.error('Collaborator user does not have access to query all greenroom file info')
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_error_msg('Permission Denied')
                    return _res.json_response()
                elif 'display_path' in query and self.current_identity['username'] not in display_path:
                    _logger.error('Collaborator user can only have access to their own file info')
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_error_msg('Permission Denied')
                    return _res.json_response()

        try:
            params = MultiDict(request.query_params)
            params['container_type'] = 'project'
            params['container_code'] = project_code

            url = ConfigClass.SEARCH_SERVICE + '/v1/metadata-items/'

            async with httpx.AsyncClient() as client:
                _logger.info(f'Calling search service {url} with query params: {params}')
                response = await client.get(url, params=params)

            if response.status_code != 200:
                _logger.error(f'Failed to query data from search service: {response.text}')
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result('Failed to query data from search service')
                return _res.json_response()

            _logger.info('Successfully Fetched file information')
            return replace_zone_labels(response.json())
        except Exception as e:
            _logger.error(f'Failed to query data from search service: {e}')
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result('Failed to query data from search service')
            return _res.json_response()
