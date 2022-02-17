from flask import request, render_template
import requests
import os
import json
import re
import datetime
from flask_jwt import jwt_required, current_identity
from resources.decorator import check_role, check_user
from resources.utils import add_user_to_ad_group, add_user_to_project_group, get_container_id, \
    remove_user_from_project_group
from flask_restx import Resource
from .namespace import users_entity_ns, datasets_entity_ns
from resources.swagger_modules import user_module, new_user_module, user_sample_return, users_sample_return
from resources.swagger_modules import permission_return, success_return
from resources.swagger_modules import dataset_sample_return, datasets_sample_return, dataset_user_status
from config import ConfigClass
from services.invitation_services.invitation_manager import SrvInvitationManager
from models.invitation import InvitationForm
from services.notifier_services.email_service import SrvEmail
from services.logger_services.logger_factory_service import SrvLoggerFactory
from services.container_services.container_manager import SrvContainerManager
from services.neo4j_service.neo4j_client import Neo4jClient
from models.user_type import map_neo4j_to_frontend
from services.permissions_service.decorators import permissions_check

# init logger
_logger = SrvLoggerFactory('api_container_user').get_logger()


class ContainerUser(Resource):

    @datasets_entity_ns.response(200, success_return)
    @jwt_required()
    @check_role("admin")
    def post(self, username, project_geid):
        """
        This method allow container admin to add single user to a specific container with permission.
        """
        _logger.info('Call API for adding user {} to project {}'.format(
            username, str(project_geid)))
        try:
            # Get token from request's header
            access_token = request.headers.get("Authorization", None)
            headers = {
                'Authorization': access_token
            }
            # Check if permission is provided
            role = request.get_json().get("role", None)
            if role is None:
                _logger.error('Error: user\'s role is required.')
                return {'result': "User's role is required."},

            query_params = {"global_entity_id": project_geid}
            container_id = get_container_id(query_params)
            if container_id is None:
                return {'result': f"Cannot find project with geid : {project_geid}"}
            # check if dataset exist
            is_dataset, res_dataset, code = validate_container(
                headers=headers, container_id=container_id)
            if not is_dataset:
                return res_dataset, code
            else:
                datasets = res_dataset

            dataset_name = datasets[0]['name']
            dataset_code = datasets[0]['code']

            # validate user and relationship
            is_users, res_users, code = validate_user(
                username=username, headers=headers)
            if not is_users:
                return res_users, code
            else:
                users = res_users

            user_id = users[0]['id']
            user_email = users[0]["email"]

            # validate user relationship
            is_related, res, code = validate_user_relationship(headers=headers, container_id=container_id,
                                                               user_id=user_id, username=username)
            user_dataset_relation = res.json()
            if len(user_dataset_relation) > 0:
                _logger.error(
                    'User %s already in the project please check.' % username)
                return {'result': 'User %s already in the project please check.' % username}, 403

            # add user to ad group
            try:
                add_user_to_ad_group(
                    user_email, dataset_code, _logger, access_token)
            except Exception as error:
                error = f'Error adding user to group {ConfigClass.AD_PROJECT_GROUP_PREFIX}{dataset_code}: ' + str(
                    error)
                _logger.info(error)
                return {'result': error}, 500

            # keycloak user role update
            is_updated, response, code = keycloak_user_role_update(
                headers, user_email, dataset_code, role)
            if not is_updated:
                return response, code
            
            # add user relationship in neo4j
            is_added, user_add_res, code = add_user_relationship(
                headers, user_id, container_id, role)
            if not is_added:
                return user_add_res, code

            # send email to user
            title = "Project %s Notification: New Invitation" % (
                str(dataset_name))
            template = "user_actions/invite.html"
            send_email_user(users, dataset_name, username,
                            role, title, template)
        except Exception as e:
            return {'result': str(e)}, 403
        return {'result': json.loads(user_add_res.text)}, 200

    @datasets_entity_ns.response(200, success_return)
    @jwt_required()
    @check_role("admin")
    def put(self, username, project_geid):
        """
        This method allow user to update user's permission to a specific dataset.
        """

        _logger.info('Call API for changing user {} role in project {}'.format(
            username, project_geid))

        try:
            # Get token from request's header
            access_token = request.headers.get("Authorization", None)
            headers = {
                'Authorization': access_token
            }
            query_params = {"global_entity_id": project_geid}
            container_id = get_container_id(query_params)

            # Check if permission is provided
            old_role = request.get_json().get("old_role", None)
            new_role = request.get_json().get("new_role", None)
            is_valid, res_valid, code = validate_payload(
                old_role=old_role, new_role=new_role, username=username)
            if not is_valid:
                return res_valid, code

            # check if dataset exist
            is_dataset, res_dataset, code = validate_container(
                headers=headers, container_id=container_id)
            if not is_dataset:
                return res_dataset, code
            else:
                datasets = res_dataset

            dataset_name = datasets[0]['name']
            dataset_code = datasets[0]['code']

            # validate user
            is_users, res_users, code = validate_user(
                username=username, headers=headers)
            if not is_users:
                return res_users, code
            else:
                users = res_users

            user_id = users[0]['id']
            user_email = users[0]["email"]

            # validate user relationship
            is_related, res, code = validate_user_relationship(headers=headers, container_id=container_id,
                                                               user_id=user_id, username=username)
            result = json.loads(res.text)
            if len(result) == 0:
                _logger.error(
                    "User %s does not exist in project." % username)
                return {'result': "User %s does not exist in project." % username}, 404

            # Update relation between user and container
            is_update, updated_res, code = update_user_relationship(
                headers, user_id, container_id, old_role, new_role)
            if not is_update:
                return updated_res, code

            # keycloak user role delete
            is_deleted, del_response, code = keycloak_user_role_delete(
                headers, user_email, dataset_code, old_role)
            if not is_deleted:
                return del_response, code

            # keycloak user role update
            is_updated, response, code = keycloak_user_role_update(
                headers, user_email, dataset_code, new_role)
            if not is_updated:
                return response, code

            # send email
            title = "Project %s Notification: Role Modified" % (
                str(dataset_name))
            template = "role/update.html"
            send_email_user(users, dataset_name, username,
                            new_role, title, template)

        except Exception as error:
            _logger.error(
                'Error in updating user\'s role info: {}'.format(str(error)))
            return {'result': str(error)}, 403

        return {'result': 'success'}, 200

    @datasets_entity_ns.response(200, success_return)
    @jwt_required()
    @check_role("admin")
    def delete(self, username, project_geid):
        """
        This method allow user to remove user's permission to a specific dataset.
        """
        _logger.info('Call API for removing user {} from project {}:'.format(
            username, project_geid))
        try:
            # Get token from request's header
            access_token = request.headers.get("Authorization", None)
            headers = {
                'Authorization': access_token
            }
            query_params = {"global_entity_id": project_geid}
            container_id = get_container_id(query_params)

            # validate user
            is_users, res_users, code = validate_user(
                username=username, headers=headers)
            if not is_users:
                return res_users, code
            else:
                users = res_users
            user_id = users[0]['id']
            user_email = users[0]["email"]

            # validate user relationship
            is_related, res, code = validate_user_relationship(headers=headers, container_id=container_id,
                                                               user_id=user_id, username=username)
            result = json.loads(res.text)
            if len(result) == 0:
                _logger.error(
                    "User %s does not exist in project." % username)
                return {'result': "User %s does not exist in project." % username}, 404
            dataset_node = result[0]["end_node"]
            role = result[0]["r"]["type"]

            # remove from ad group
            remove_user_from_project_group(
                container_id, user_email, _logger, access_token)

            is_delete, res_delete, code = delete_relation_user_container(
                user_id=user_id, container_id=container_id)
            if not is_delete:
                return res_delete, code

            # keycloak user role delete
            dataset_code = dataset_node["code"]
            is_deleted, del_response, code = keycloak_user_role_delete(
                headers, user_email, dataset_code, role)
            if not is_deleted:
                return del_response, code

        except Exception as e:
            _logger.error(
                'Error in removing user: {}'.format(str(e)))
            return {'result': str(e)}, 403
        return {'result': 'success'}, 200


def delete_relation_user_container(user_id, container_id):
    # Get relation between user and container
    neo4j_relation_url = ConfigClass.NEO4J_SERVICE + \
        f"relations?start_id={int(user_id)}&end_id={int(container_id)}"

    res = requests.get(url=neo4j_relation_url)
    if res.status_code != 200 or len(json.loads(res.text)) == 0:
        return False, {'result': "No relation found."}, res.status_code

    # Delete relation between user and container
    res = requests.delete(url=neo4j_relation_url)
    if res.status_code != 200:
        _logger.error('neo4j service: {}'.format(json.loads(res.text)))
        return False, {'result': json.loads(res.text)}, res.status_code
    return True, {}, 200


def validate_payload(old_role, new_role, username):
    if old_role is None or new_role is None:
        _logger.error("User's old and new role is required.")
        return False, {'result': "User's old and new role is required."}, 403
    # Check if user is themself
    current_user = current_identity["username"]
    if current_user == username:
        _logger.error("User cannot change their own role.")
        return False, {'result': "User cannot change their own role."}, 403
    return True, {}, 200


def keycloak_user_role_delete(headers, user_email, dataset_code, role):
    payload = {
        "realm": ConfigClass.KEYCLOAK_REALM,
        "email": user_email,
        "project_role": dataset_code + "-" + role,
    }
    response = requests.delete(
        ConfigClass.AUTH_SERVICE + "user/project-role", json=payload, headers=headers)
    if response.status_code != 200:
        return False, {'result': "Error assigning project role" + str(response.text)}, response.status_code
    return True, None, 200


def keycloak_user_role_update(headers, user_email, dataset_code, role):
    payload = {
        "realm": ConfigClass.KEYCLOAK_REALM,
        "email": user_email,
        "project_role": dataset_code + "-" + role,
    }
    response = requests.post(
        ConfigClass.AUTH_SERVICE + "user/project-role", json=payload, headers=headers)
    if response.status_code != 200:
        return False, {'result': "Error assigning project role" + str(response.text)}, response.status_code
    return True, None, 200


def send_email_user(users, dataset_name, username, role, title, template):
    try:
        email = users[0]['email']
        admin_name = current_identity["username"]
        title = title
        SrvEmail().send(
            title,
            [email],
            msg_type="html",
            template=template,
            template_kwargs={
                "username": username,
                "admin_name": admin_name,
                "project_name": dataset_name,
                "role": map_neo4j_to_frontend(role),
                "login_url": ConfigClass.INVITATION_URL_LOGIN,
                "admin_email": ConfigClass.EMAIL_ADMIN,
                "support_email": ConfigClass.EMAIL_SUPPORT,
            },
        )
    except Exception as e:
        _logger.error('email service: {}'.format(str(e)))


def validate_container(headers, container_id):
    # Check if dataset exist
    url = ConfigClass.NEO4J_SERVICE + "nodes/Container/node/" + container_id
    res = requests.get(
        url=url,
        headers=headers
    )
    datasets = json.loads(res.text)
    if len(datasets) == 0:
        _logger.error("Container %s is not available." % container_id)
        return False, {'result': "Container %s is not available." % container_id}, 404

    if 'type' in datasets[0] and datasets[0]['type'] == "default":
        _logger.error('Container %s is default.' % container_id)
        return False, {'result': "Container %s is default." % container_id}, 403

    return True, datasets, 200


def validate_user(headers, username):
    url = ConfigClass.NEO4J_SERVICE + "nodes/User/query"
    res = requests.post(
        url=url,
        headers=headers,
        json={"name": username}
    )
    users = json.loads(res.text)
    if len(users) == 0:
        _logger.error('User %s does not exist.' % username)
        return False, {'result': "User %s does not exist." % username}, 403
    return True, users, 200


def validate_user_relationship(headers, user_id, container_id, username):
    url = ConfigClass.NEO4J_SERVICE + "relations/query"
    res = requests.post(
        url=url,
        headers=headers,
        json={
            'start_label': 'User',
            'start_params': {'id': user_id},
            'end_label': 'Container',
            'end_params': {'id': int(container_id)},
        }
    )
    if res.status_code != 200:
        return False, {'result': res.text}, res.status_code
    # user_dataset_relation = res.json()
    return True, res, 200


def add_user_relationship(headers, user_id, container_id, role):
    url = ConfigClass.NEO4J_SERVICE + "relations/" + role
    res = requests.post(
        url=url,
        headers=headers,
        json={
            "start_id": int(user_id),
            "end_id": int(container_id),
            "properties": {
                "status": "active"
            }
        }
    )
    if res.status_code != 200:
        _logger.error('neo4j service: {}'.format(json.loads(res.text)))
        return False, {'result': json.loads(res.text)}, res.status_code
    return True, res, 200


def update_user_relationship(headers, user_id, container_id, old_role, new_role):
    url = ConfigClass.NEO4J_SERVICE + "relations/" + old_role
    res = requests.put(
        url=url,
        headers=headers,
        json={
            "start_id": int(user_id),
            "end_id": int(container_id),
            "new_label": new_role
        }
    )
    if res.status_code != 200:
        _logger.error('neo4j service: {}'.format(json.loads(res.text)))
        return False, {'result': json.loads(res.text)}, res.status_code
    return True, {}, 200
