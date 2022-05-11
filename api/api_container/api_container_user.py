import json

import requests
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource

from config import ConfigClass
from models.user_type import map_neo4j_to_frontend
from resources.error_handler import APIException
from resources.swagger_modules import success_return
from resources.utils import (add_user_to_ad_group, get_container_id,
                             remove_user_from_project_group)
from common import LoggerFactory
from services.notifier_services.email_service import SrvEmail
from services.permissions_service.decorators import permissions_check
from services.permissions_service.utils import get_project_role

from .namespace import datasets_entity_ns

# init logger
_logger = LoggerFactory('api_container_user').get_logger()


class ContainerUser(Resource):

    @datasets_entity_ns.response(200, success_return)
    @jwt_required()
    @permissions_check('invite', '*', 'create')
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
            containers= get_container_by_id(container_id)
            container_name = containers[0]['name']
            container_code = containers[0]['code']

            # validate user and relationship
            user = validate_user(username)

            user_id = user['id']
            user_email = user["email"]

            # add user to ad group
            if user["role"] != "admin":
                try:
                    add_user_to_ad_group(user_email, container_code, _logger)
                except Exception as error:
                    error = f'Error adding user to group {ConfigClass.AD_PROJECT_GROUP_PREFIX}{container_code}: ' + str(
                        error)
                    _logger.info(error)
                    return {'result': error}, 500

            # keycloak user role update
            is_updated, response, code = keycloak_user_role_update(
                "add",
                user_email,
                f"{container_code}-{role}",
                container_code,
                current_identity["username"],
            )
            if not is_updated:
                return response, code

            # send email to user
            title = "Project %s Notification: New Invitation" % (
                str(container_name))
            template = "user_actions/invite.html"
            send_email_user(user, container_name, username, role, title, template)
        except Exception as e:
            raise e
            return {'result': str(e)}, 403
        return {'result': 'success'}, 200

    @datasets_entity_ns.response(200, success_return)
    @jwt_required()
    @permissions_check('users', '*', 'view')
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

            # check if container exist
            containers = get_container_by_id(container_id)
            container_name = containers[0]['name']
            container_code = containers[0]['code']

            # validate user
            user = validate_user(username)

            user_id = user['id']
            user_email = user["email"]

            # keycloak user role update
            is_updated, response, code = keycloak_user_role_update(
                "change",
                user_email,
                f"{container_code}-{new_role}",
                container_code,
                current_identity["username"]
            )
            if not is_updated:
                return response, code

            # send email
            title = "Project %s Notification: Role Modified" % (str(container_name))
            template = "role/update.html"
            send_email_user(user, container_name, username, new_role, title, template)
        except Exception as error:
            _logger.error(
                'Error in updating user\'s role info: {}'.format(str(error)))
            return {'result': str(error)}, 403

        return {'result': 'success'}, 200

    @datasets_entity_ns.response(200, success_return)
    @jwt_required()
    @permissions_check('users', '*', 'view')
    def delete(self, username, project_geid):
        """
        This method allow user to remove user's permission to a specific container.
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
            user = validate_user(username)
            user_id = user['id']
            user_email = user["email"]

            # get project info
            containers = get_container_by_id(container_id)
            container_node = containers[0]
            container_code = container_node.get("code")
            # print("=====", current_identity)
            # role = get_project_role(container_node["code"])
            response = requests.get(ConfigClass.AUTH_SERVICE + "admin/users/realm-roles", \
                params={"username": username}, headers=headers)
            if response.status_code != 200:
                raise Exception(str(response.__dict__))
            # find out the permission of user
            project_role = None
            user_roles = response.json().get("result", [])
            for role in user_roles:
                if container_code in role.get("name"):
                    project_role = role.get("name").replace(container_code + "-", "")
            # raise the error if user has no permission
            if not project_role:
                raise Exception("Cannot find user permission in project")

            # remove from ad group
            remove_user_from_project_group(container_id, user_email, _logger, access_token)
            # keycloak user role delete
            keycloak_user_role_delete(
                user_email,
                f"{container_code}-{project_role}",
                container_code,
                current_identity["username"]
            )


        except Exception as e:
            _logger.error(
                'Error in removing user: {}'.format(str(e)))
            return {'result': str(e)}, 400
        return {'result': 'success'}, 200


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


def keycloak_user_role_delete(user_email: str, role: str, project_code: str, operator: str):
    payload = {
        "realm": ConfigClass.KEYCLOAK_REALM,
        "email": user_email,
        "project_role": role,
        "project_code": project_code,
        "operator": operator,
    }
    response = requests.delete(ConfigClass.AUTH_SERVICE + "user/project-role", json=payload)
    if response.status_code != 200:
        raise Exception("Error assigning project role" + str(response.__dict__))
    return response


def keycloak_user_role_update(operation: str, user_email: str, role: str, project_code: str, operator: str):
    payload = {
        "realm": ConfigClass.KEYCLOAK_REALM,
        "email": user_email,
        "project_role": role,
        "project_code": project_code,
        "operator": operator,
    }
    if operation == "add":
        payload["invite_event"] = True
        response = requests.post(ConfigClass.AUTH_SERVICE + "user/project-role", json=payload)
    else:
        response = requests.put(ConfigClass.AUTH_SERVICE + "user/project-role", json=payload)
    if response.status_code != 200:
        return False, {'result': "Error assigning project role" + str(response.text)}, response.status_code
    return True, None, 200


def send_email_user(user, dataset_name, username, role, title, template):
    try:
        email = user['email']
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


def get_container_by_id(container_id):
    # Check if container exist
    url = ConfigClass.NEO4J_SERVICE + "nodes/Container/node/" + container_id
    res = requests.get(
        url=url,
    )
    datasets = res.json()
    if not datasets:
        error_msg = f"Container {container_id} is not available."
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg=error_msg)
    return datasets


def validate_user(username: str) -> dict:
    payload = {"username": username}
    response = requests.get(ConfigClass.AUTH_SERVICE + "admin/user", params=payload)
    if not response.json()["result"]:
        raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg="User not found")
    return response.json()["result"]
