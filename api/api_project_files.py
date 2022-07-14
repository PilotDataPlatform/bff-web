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

from common import LoggerFactory
from common import ProjectClient
from common.project.project_client import ProjectObject
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from starlette.datastructures import MultiDict

from app.auth import jwt_required
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.permissions_service.utils import get_project_role
from services.search.client import SearchServiceClient
from services.search.client import get_search_service_client

_logger = LoggerFactory('api_project_files').get_logger()

router = APIRouter(prefix='/project-files', tags=['Project Files'], dependencies=[Depends(jwt_required)])


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


async def get_project(project_code: str) -> ProjectObject:
    """Get project by code as a dependency."""

    project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
    return await project_client.get(code=project_code)


@router.get('/{project_code}/search', summary='Search through project files.')
async def search(
    request: Request,
    current_identity: Dict[str, Any] = Depends(jwt_required),
    project: ProjectObject = Depends(get_project),
    search_service_client: SearchServiceClient = Depends(get_search_service_client),
):
    """Search through project files."""

    response = APIResponse()

    if current_identity['role'] != 'admin':
        project_role = get_project_role(project.code, current_identity)

        response.set_code(EAPIResponseCode.forbidden)
        response.set_error_msg('Not implemented.')
        return response.json_response()

        # TODO: Revise this in connection with search service
        if project_role == 'contributor':
            # Make sure contributor is restrict to querying there own files/folders
            # the reason use display_path is all own files/folders under user's name folder
            if 'display_path' not in query:
                _logger.error('Non-admin user does not have access to query all user file info')
                response.set_code(EAPIResponseCode.forbidden)
                response.set_error_msg(
                    'Permission Denied, Non-admin user does not have access to query all user file info'
                )
                return response.json_response()
            elif current_identity['username'] not in query['display_path']['value']:
                _logger.error('Non-admin user can only have access to their own file info')
                response.set_code(EAPIResponseCode.forbidden)
                response.set_error_msg('Permission Denied, Non-admin user can only have access to their own file info')
                return response.json_response()
            elif 'zone' not in query:
                _logger.error('Zone and file_type is required if user role is contributor')
                response.set_code(EAPIResponseCode.forbidden)
                response.set_error_msg('Permission Denied, zone and file_type is required if user role is contributor')
                return response.json_response()
            elif query['zone']['value'] == 'core':
                _logger.error('Contributor cannot fetch core files or processed files')
                response.set_code(EAPIResponseCode.forbidden)
                response.set_error_msg('Permission Denied, contributor cannot fetch core files or processed files')
                return response.json_response()
        elif project_role == 'collaborator':
            display_path = query['display_path']['value']
            if query['zone']['value'] == 'greenroom' and 'display_path' not in query:
                _logger.error('Collaborator user does not have access to query all greenroom file info')
                response.set_code(EAPIResponseCode.forbidden)
                response.set_error_msg('Permission Denied')
                return response.json_response()
            elif 'display_path' in query and current_identity['username'] not in display_path:
                _logger.error('Collaborator user can only have access to their own file info')
                response.set_code(EAPIResponseCode.forbidden)
                response.set_error_msg('Permission Denied')
                return response.json_response()

    try:
        params = MultiDict(request.query_params)
        params['container_type'] = 'project'
        params['container_code'] = project.code
        result = await search_service_client.get_metadata_items(params)
        _logger.info('Successfully fetched data from search service')
        return replace_zone_labels(result)
    except Exception as e:
        _logger.error(f'Failed to query data from search service: {e}')
        response.set_code(EAPIResponseCode.internal_error)
        response.set_result('Failed to query data from search service')
        return response.json_response()


@router.get('/{project_code}/size', summary='Get project storage usage.')
async def size(
    request: Request,
    current_identity: Dict[str, Any] = Depends(jwt_required),
    project: ProjectObject = Depends(get_project),
    search_service_client: SearchServiceClient = Depends(get_search_service_client),
):
    """Get project storage usage."""

    try:
        params = MultiDict(request.query_params)
        result = await search_service_client.get_project_size(project.code, params)
        _logger.info('Successfully fetched data from search service')
        return result
    except Exception as e:
        _logger.error(f'Failed to query data from search service: {e}')
        response = APIResponse()
        response.set_code(EAPIResponseCode.internal_error)
        response.set_result('Failed to query data from search service')
        return response.json_response()


@router.get('/{project_code}/statistics', summary='Get project statistics on files and transfer activity.')
async def statistics(
    request: Request,
    current_identity: Dict[str, Any] = Depends(jwt_required),
    project: ProjectObject = Depends(get_project),
    search_service_client: SearchServiceClient = Depends(get_search_service_client),
):
    """Get project statistics on files and transfer activity."""

    try:
        params = MultiDict(request.query_params)
        result = await search_service_client.get_project_statistics(project.code, params)
        _logger.info('Successfully fetched data from search service')
        return result
    except Exception as e:
        _logger.error(f'Failed to query data from search service: {e}')
        response = APIResponse()
        response.set_code(EAPIResponseCode.internal_error)
        response.set_result('Failed to query data from search service')
        return response.json_response()


@router.get('/{project_code}/activity', summary='Get project file activity statistic.')
async def activity(
    request: Request,
    current_identity: Dict[str, Any] = Depends(jwt_required),
    project: ProjectObject = Depends(get_project),
    search_service_client: SearchServiceClient = Depends(get_search_service_client),
):
    """Get project file activity statistic."""

    try:
        params = MultiDict(request.query_params)
        result = await search_service_client.get_project_activity(project.code, params)
        _logger.info('Successfully fetched data from search service')
        return result
    except Exception as e:
        _logger.error(f'Failed to query data from search service: {e}')
        response = APIResponse()
        response.set_code(EAPIResponseCode.internal_error)
        response.set_result('Failed to query data from search service')
        return response.json_response()
