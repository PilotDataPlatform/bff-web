import requests
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource
from common import LoggerFactory

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
from services.neo4j_service.neo4j_client import Neo4jClient
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
            neo4j_client = Neo4jClient()
            relation_data = post_json.get('relationship', {})

            _logger.info(f'Start Creating Invitation: {post_json}')

            project_node = None
            if relation_data:
                response = neo4j_client.get_container_by_geid(relation_data.get('project_geid'))
                if response.get('code') != 200:
                    return response, response.get('code')
                project_node = response['result']

            if not check_invite_permissions(project_node, current_identity):
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
            neo4j_client = Neo4jClient()

            if current_identity['role'] != 'admin' and not project_geid:
                my_res.set_result('Permission denied')
                my_res.set_code(EAPIResponseCode.unauthorized)
                return my_res.to_dict, my_res.code

            if project_geid:
                response = neo4j_client.get_container_by_geid(project_geid)
                if response.get('code') == 404:
                    my_res.set_result('Container does not exist in platform')
                    my_res.set_code(EAPIResponseCode.not_found)
                    return my_res.to_dict, my_res.code
                elif response.get('code') != 200:
                    return response
                project_node = response['result']

                if not has_permission(project_node['code'], 'invite', '*', 'create'):
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
                neo4j_client = Neo4jClient()
                response = neo4j_client.get_container_by_geid(project_geid)
                if response.get('code') == 404:
                    my_res.set_result('Container does not exist in platform')
                    my_res.set_code(EAPIResponseCode.not_found)
                    return my_res.to_dict, my_res.code
                elif response.get('code') != 200:
                    return response
                project_node = response['result']
                if not has_permission(project_node['code'], 'invite', '*', 'view'):
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
