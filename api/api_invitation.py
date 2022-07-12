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
from common import LoggerFactory, ProjectClient
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from resources.error_handler import APIException
from resources.utils import check_invite_permissions
from services.permissions_service.utils import has_permission

router = APIRouter(tags=["Invitations"])


@cbv.cbv(router)
class InvitationsRestful:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/invitations',
        summary="create invitation in platform",
    )
    async def post(self, request: Request):
        """This method allow to create invitation in platform."""
        _logger = LoggerFactory('api_invitation').get_logger()
        my_res = APIResponse()
        post_json = await request.json()
        relation_data = post_json.get('relationship', {})

        _logger.info(f'Start Creating Invitation: {post_json}')

        if relation_data:
            project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
            project = await project_client.get(id=relation_data.get('project_geid'))

            if not check_invite_permissions(await project.json(), self.current_identity):
                my_res.set_result('Permission denied')
                my_res.set_code(EAPIResponseCode.forbidden)
                return my_res.json_response()

        try:
            post_json['invited_by'] = self.current_identity['username']
            response = requests.post(ConfigClass.AUTH_SERVICE + 'invitations', json=post_json)
        except Exception as e:
            error_msg = f'Error calling Auth service for invite create: {e}'
            _logger.error(error_msg)
            raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class CheckUserPlatformRole:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/invitation/check/{email}',
        summary="Check if a user exists",
    )
    async def get(self, email: str, request: Request):
        my_res = APIResponse()
        _logger = LoggerFactory('api_invitation').get_logger()
        project_id = request.query_params.get('project_id')

        if self.current_identity['role'] != 'admin' and not project_id:
            my_res.set_result('Permission denied')
            my_res.set_code(EAPIResponseCode.unauthorized)
            return my_res.json_response()

        params = {}
        if project_id:
            project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
            project = await project_client.get(id=project_id)

            if not has_permission(project.code, 'invite', '*', 'create', self.current_identity):
                my_res.set_result('Permission denied')
                my_res.set_code(EAPIResponseCode.unauthorized)
                return my_res.json_response()
            params["project_code"] = project.code
        try:
            response = requests.get(ConfigClass.AUTH_SERVICE + f'invitation/check/{email}', params=params)
        except Exception as e:
            error_msg = f'Error calling Auth service for invite check: {e}'
            _logger.error(error_msg)
            raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class PendingUserRestful:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/invitation-list',
        summary="list invitations",
    )
    async def post(self, request: Request):
        """This method allow to get all pending users from invitation links."""
        _logger = LoggerFactory('api_pending_users').get_logger()
        _logger.info('fetching pending user api triggered')
        my_res = APIResponse()
        post_json = await request.json()

        filters = post_json.get('filters', None)
        project_id = filters.get('project_id', None)

        if self.current_identity['role'] != 'admin':
            project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
            project = await project_client.get(id=project_id)
            if not has_permission(project.code, 'invite', '*', 'view', self.current_identity):
                my_res.set_code(EAPIResponseCode.forbidden)
                my_res.set_error_msg('Permission denied')
                return my_res.json_response()
        try:
            response = requests.post(ConfigClass.AUTH_SERVICE + 'invitation-list/', json=post_json)
        except Exception as e:
            error_msg = f'Error calling Auth service for invite list: {e}'
            _logger.error(error_msg)
            raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
        return JSONResponse(content=response.json(), status_code=response.status_code)
