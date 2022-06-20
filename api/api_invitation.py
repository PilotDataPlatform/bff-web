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
from common import LoggerFactory, ProjectClientSync

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
from models.api_response import APIResponse, EAPIResponseCode
from resources.error_handler import APIException
from resources.swagger_modules import (
    create_invitation_request_model,
    create_invitation_return_example,
)
from resources.utils import check_invite_permissions
from services.permissions_service.utils import has_permission

api_ns_invitations = module_api.namespace('Invitation Restful', description='Portal Invitation Restful', path='/v1')
api_ns_invitation = module_api.namespace('Invitation Restful', description='Portal Invitation Restful', path='/v1')


class APIInvitation(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_invitations.add_resource(self.InvitationsRestful, '/invitations')
        api_ns_invitation.add_resource(self.CheckUserPlatformRole, '/invitation/check/<email>')
        api_ns_invitation.add_resource(self.PendingUserRestful, '/invitation-list')

    class InvitationsRestful(Resource):
        @api_ns_invitations.expect(create_invitation_request_model)
        @api_ns_invitations.response(200, create_invitation_return_example)
        @jwt_required()
        def post(self):
            """This method allow to create invitation in platform."""
            _logger = LoggerFactory('api_invitation').get_logger()
            my_res = APIResponse()
            post_json = request.get_json()
            relation_data = post_json.get('relationship', {})

            _logger.info(f'Start Creating Invitation: {post_json}')

            if relation_data:
                project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
                project = project_client.get(id=relation_data.get('project_geid'))

                if not check_invite_permissions(project.json(), current_identity):
                    my_res.set_result('Permission denied')
                    my_res.set_code(EAPIResponseCode.forbidden)
                    return my_res.to_dict, my_res.code

            try:
                post_json['invited_by'] = current_identity['username']
                response = requests.post(ConfigClass.AUTH_SERVICE + 'invitations', json=post_json)
            except Exception as e:
                error_msg = f'Error calling Auth service for invite create: {e}'
                _logger.error(error_msg)
                raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
            return response.json(), response.status_code

    class CheckUserPlatformRole(Resource):
        @jwt_required()
        def get(self, email):
            """This method allow to get user's detail on the platform."""
            my_res = APIResponse()
            _logger = LoggerFactory('api_invitation').get_logger()
            project_geid = request.args.get('project_geid')

            if current_identity['role'] != 'admin' and not project_geid:
                my_res.set_result('Permission denied')
                my_res.set_code(EAPIResponseCode.unauthorized)
                return my_res.to_dict, my_res.code

            if project_geid:
                project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
                project = project_client.get(id=project_geid)

                if not has_permission(project.code, 'invite', '*', 'create'):
                    my_res.set_result('Permission denied')
                    my_res.set_code(EAPIResponseCode.unauthorized)
                    return my_res.to_dict, my_res.code
            try:
                response = requests.get(ConfigClass.AUTH_SERVICE + f'invitation/check/{email}', params=request.args)
            except Exception as e:
                error_msg = f'Error calling Auth service for invite check: {e}'
                _logger.error(error_msg)
                raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
            return response.json(), response.status_code

    class PendingUserRestful(Resource):
        @jwt_required()
        def post(self):
            """This method allow to get all pending users from invitation links."""
            _logger = LoggerFactory('api_pending_users').get_logger()
            _logger.info('fetching pending user api triggered')
            my_res = APIResponse()
            post_json = request.get_json()

            filters = post_json.get('filters', None)
            project_geid = filters.get('project_id', None)

            if current_identity['role'] != 'admin':
                project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
                project = project_client.get(id=project_geid)
                if not has_permission(project.code, 'invite', '*', 'view'):
                    my_res.set_code(EAPIResponseCode.forbidden)
                    my_res.set_error_msg('Permission denied')
                    return my_res.to_dict, my_res.code
            try:
                response = requests.post(ConfigClass.AUTH_SERVICE + 'invitation-list/', json=post_json)
            except Exception as e:
                error_msg = f'Error calling Auth service for invite list: {e}'
                _logger.error(error_msg)
                raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
            return response.json(), response.status_code
