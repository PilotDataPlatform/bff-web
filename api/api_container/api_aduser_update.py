from flask import request, render_template
import requests
import re
from flask_jwt import jwt_required, current_identity
from resources.utils import *
from flask_restx import Resource
from .namespace import users_entity_ns
from resources.swagger_modules import new_user_module, user_sample_return, users_sample_return
from config import ConfigClass
from services.invitation_services.invitation_manager import SrvInvitationManager
from services.notifier_services.email_service import SrvEmail
from services.logger_services.logger_factory_service import SrvLoggerFactory
from services.container_services.container_manager import SrvContainerManager
from services.neo4j_service.neo4j_client import Neo4jClient
from models.user_type import map_neo4j_to_frontend
from services.permissions_service.decorators import permissions_check
import ldap

# init logger
_logger = SrvLoggerFactory('api_aduser_update').get_logger()


class ADUserUpdate(Resource):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.neo4j_client = Neo4jClient()

    @users_entity_ns.expect(new_user_module)
    @users_entity_ns.response(200, user_sample_return)
    def put(self):
        """
        This method allow user to activate the AD user account on platform.
        """
        try:
            # validate payload request body
            post_data = request.get_json()
            _logger.info(
                'Calling API for updating AD user: {}'.format(post_data))
            # Get current user info
            # Request payload validation
            email = post_data.get('email', None)
            username = post_data.get("username", None)
            first_name = post_data.get("first_name", None)
            last_name = post_data.get("last_name", None)
            status = post_data.get("status", "active")
            access_token = request.headers.get("Authorization", None)
            if not access_token:
                return {'result': 'Token required'}, 400

            if not username or not first_name or not last_name \
                    or not email:
                _logger.error(
                    '[UserUpdateByEmail] Require field email/username/first_name/last_name.')
                return {'result': 'Required information is not sufficient.'}, 400

            # get_user
            user_data_query_results = self.get_user(email=email)
            if user_data_query_results['code'] == 404:
                return {'result': 'User not found'}, 403
            elif user_data_query_results['code'] != 200:
                return user_data_query_results, user_data_query_results['code']
            user_data = user_data_query_results['result']
            _logger.info("Current user data: %s", user_data)
            if user_data_query_results['code'] == 200:
                user_data = user_data_query_results['result']

            email = email.lower()
            if status == 'active':
                if user_data["role"] == "admin":
                    self.assign_user_role_ad("platform-admin", email=email)
                    self.bulk_create_name_folder_admin(username)
                else:
                    respon_linked_projects = self.neo4j_client.get_user_linked_projects(
                        user_data['id'])
                    if respon_linked_projects.status_code == 200:
                        linked_projects = [self.decode_linked_projects(
                            record) for record in respon_linked_projects.json()]
                        to_assigned_roles = list(
                            set([project_info['ad_role'] for project_info in linked_projects]))
                        for role in to_assigned_roles:
                            self.assign_user_role_ad(role, email=email)
                        project_code_list = [details['end_node']['code'] for details in respon_linked_projects.json()]
                        self.bulk_create_folder(
                            folder_name=username, project_code_list=project_code_list)

            self.update_invitation(email)
            user_info = {
                "status": status,
                "username": username,
                "first_name": first_name,
                "last_name": last_name
            }
            return self.update_user_neo4j(user_data=user_data, user_info=user_info)
        except Exception as error:
            _logger.error(f"Error when updating user data : {error}")
            raise (Exception(f'Internal error when updating user data : {error}'))

    @staticmethod
    def update_invitation(email):
        query_data = {
            "email": email,
        }
        update_data = {"status": "complete"}
        invitation_mgr = SrvInvitationManager()
        response = invitation_mgr.update_invitation(
            query_data, update_data)
        if response != 'success':
            return {'result': str(response)}, 500
        _logger.info('update invitation successfully')

    def update_user_neo4j(self, user_data, user_info):
        user_data['username'] = user_info['username']
        user_data['name'] = user_info['username']
        user_data['first_name'] = user_info['first_name']
        user_data['last_name'] = user_info['last_name']
        user_data['status'] = user_info['status']
        update_results = self.neo4j_client.update_user(
            user_data['id'], user_data)
        _logger.info('Update user in neo4j results: %s', update_results)
        if update_results['code'] == 200:
            updated = update_results['result'][0]
            return {"result": updated}, 200
        else:
            _logger.info('Done with updating user node to neo4j')
            raise (Exception('Internal error when updating user data'))

    def get_user(self, email):
        # get user
        user_data_query_results = self.neo4j_client.get_user_by_email(email)
        return user_data_query_results

    # the fucntion is not used
    def add_admin_projects(self, username):
        # Give platform admin admin role for each project
        payload = {
            "realm": ConfigClass.KEYCLOAK_REALM,
            "username": username,
        }
        response = requests.post(
            ConfigClass.AUTH_SERVICE + "admin/users/project-role/all", json=payload)
        if response.status_code != 200:
            _logger.error('Error adding user to all groups')
            return {'result': response.json()}, response.status_code
        _logger.info(
            "Creating user namespace folder for all projects")
        # self.create_usernamespace_folder_admin(username=username)
        is_created = self.bulk_create_name_folder_admin(
            username)

        if is_created:
            return {'result': 'user has been created'}, 400

    @staticmethod
    def decode_linked_projects(project_queried):
        project_info = project_queried['end_node']
        relation = project_queried['r']
        decoded = {
            "project_code": project_info['code'],
            "relation_name": relation['type'],
            'relation_status': relation['status'],
            "ad_role": "{}-{}".format(project_info['code'], relation['type'])
        }
        return decoded

    @staticmethod
    def assign_user_role_ad(role: str, email):
        url = ConfigClass.AUTH_SERVICE + "user/project-role"
        request_payload = {
            "email": email,
            "realm": ConfigClass.KEYCLOAK_REALM,
            "project_role": role
        }
        response_assign = requests.post(
            url, json=request_payload)
        if response_assign.status_code != 200:
            raise Exception('[Fatal]Assigned project_role Failed: {}: {}: {}'.format(email,
                                                                                     role,
                                                                                     response_assign.text))

    @staticmethod
    def bulk_create_folder(folder_name, project_code_list):
        try:
            _logger.info(
                f"bulk creating namespace folder in greenroom and core for user : {folder_name} under {project_code_list}")
            zone_list = ["greenroom", "core"]
            for zone in zone_list:
                payload = {
                    "folder_name": folder_name,
                    "project_code_list": project_code_list,
                    "zone": zone,
                    "uploader": folder_name,
                    "tags": []
                }
                bulk_folder_creation_url = ConfigClass.DATA_UPLOAD_SERVICE_GREENROOM + '/folder/batch'
                res = requests.post(
                    url=bulk_folder_creation_url,
                    json=payload
                )
                if res.status_code == 200:
                    _logger.info(
                        f"In namespace: {zone}, folders bulk created successfully for user : {folder_name} under {project_code_list}")
        except Exception as error:
            _logger.error(
                f"Error while trying to create namespace folder for user : {folder_name} under {project_code_list} : {error}")

    def bulk_create_name_folder_admin(self, username):
        try:
            project_code_list = []
            url = ConfigClass.NEO4J_SERVICE + 'nodes/Container/query'
            res = requests.post(url, json={})
            if res.status_code == 200 and len(res.json()) > 0:
                for project in res.json():
                    project_code = project["code"]
                    project_code_list.append(project_code)

            relations = self.neo4j_client.get_project_linked_folders(
                project_code_list[0])
            is_user_exist = False
            for relation in relations:
                if relation["end_node"]["folder_level"] == 0 and relation["end_node"]["name"] == username:
                    is_user_exist = True
            if is_user_exist:
                return True
            self.bulk_create_folder(
                folder_name=username, project_code_list=project_code_list)
            return False
        except Exception as error:
            _logger.error(f"Error while querying Container details : {error}")

