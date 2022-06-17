import requests
from common import LoggerFactory, ProjectClientSync
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource

from config import ConfigClass
from models.api_response import EAPIResponseCode
from models.user_type import map_role_to_frontend
from resources.error_handler import APIException
from resources.swagger_modules import success_return
from resources.utils import (add_user_to_ad_group, remove_user_from_project_group)
from services.notifier_services.email_service import SrvEmail
from services.permissions_service.decorators import permissions_check

from .namespace import datasets_entity_ns

# init logger
logger = LoggerFactory('api_container_user').get_logger()


class ContainerUser(Resource):

    @jwt_required()
    @permissions_check('invite', '*', 'create')
    def post(self, username, project_id):
        """
        This method allow container admin to add single user to a specific container with permission.
        """
        logger.info('Call API for adding user {} to project {}'.format(username, str(project_id)))

        # Check if permission is provided
        role = request.get_json().get("role", None)
        if role is None:
            logger.error('Error: user\'s role is required.')
            return {'result': "User's role is required."},

        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = project_client.get(id=project_id)

        # validate user and relationship
        user = validate_user(username)
        user_email = user["email"]

        # add user to ad group
        if user["role"] != "admin":
            try:
                add_user_to_ad_group(user_email, project.code, logger)
            except Exception as error:
                error = f'Error adding user to group {ConfigClass.AD_PROJECT_GROUP_PREFIX}{project.code}: ' + str(
                    error)
                logger.info(error)
                return {'result': error}, 500

        # keycloak user role update
        is_updated, response, code = keycloak_user_role_update(
            "add",
            user_email,
            f"{project.code}-{role}",
            project.code,
            current_identity["username"],
        )
        if not is_updated:
            return response, code

        # send email to user
        title = f"Project {project.code} Notification: New Invitation"
        template = "user_actions/invite.html"
        send_email_user(user, project.name, username, role, title, template)
        return {'result': 'success'}, 200

    @datasets_entity_ns.response(200, success_return)
    @jwt_required()
    @permissions_check('users', '*', 'view')
    def put(self, username, project_id):
        """
        This method allow user to update user's permission to a specific dataset.
        """

        logger.info(f'Call API for changing user {username} role in project {project_id}')

        old_role = request.get_json().get("old_role", None)
        new_role = request.get_json().get("new_role", None)
        is_valid, res_valid, code = validate_payload(old_role=old_role, new_role=new_role, username=username)
        if not is_valid:
            return res_valid, code

        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = project_client.get(id=project_id)

        # validate user
        user = validate_user(username)
        user_email = user["email"]

        # keycloak user role update
        is_updated, response, code = keycloak_user_role_update(
            "change",
            user_email,
            f"{project.code}-{new_role}",
            project.code,
            current_identity["username"]
        )
        if not is_updated:
            return response, code

        # send email
        title = f"Project {project.name} Notification: Role Modified"
        template = "role/update.html"
        send_email_user(user, project.name, username, new_role, title, template)
        return {'result': 'success'}, 200

    @datasets_entity_ns.response(200, success_return)
    @jwt_required()
    @permissions_check('users', '*', 'view')
    def delete(self, username, project_id):
        """
        This method allow user to remove user's permission to a specific container.
        """
        logger.info(f'Call API for removing user {username} from project {project_id}')

        user = validate_user(username)
        user_email = user["email"]

        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = project_client.get(id=project_id)
        response = requests.get(ConfigClass.AUTH_SERVICE + "admin/users/realm-roles", params={"username": username})
        if response.status_code != 200:
            raise Exception(str(response.__dict__))

        # find out the permission of user
        project_role = None
        user_roles = response.json().get("result", [])
        for role in user_roles:
            if project.code in role.get("name"):
                project_role = role.get("name").replace(project.code + "-", "")

        if not project_role:
            raise Exception("Cannot find user permission in project")

        # remove from ad group
        remove_user_from_project_group(project.code, user_email, logger)
        # keycloak user role delete
        keycloak_user_role_delete(
            user_email,
            f"{project.code}-{project_role}",
            project.code,
            current_identity["username"]
        )
        return {'result': 'success'}, 200


def validate_payload(old_role, new_role, username):
    if old_role is None or new_role is None:
        logger.error("User's old and new role is required.")
        return False, {'result': "User's old and new role is required."}, 403
    # Check if user is themself
    current_user = current_identity["username"]
    if current_user == username:
        logger.error("User cannot change their own role.")
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
                "role": map_role_to_frontend(role),
                "login_url": ConfigClass.INVITATION_URL_LOGIN,
                "admin_email": ConfigClass.EMAIL_ADMIN,
                "support_email": ConfigClass.EMAIL_SUPPORT,
            },
        )
    except Exception as e:
        logger.error('email service: {}'.format(str(e)))


def validate_user(username: str) -> dict:
    payload = {"username": username}
    response = requests.get(ConfigClass.AUTH_SERVICE + "admin/user", params=payload)
    if not response.json()["result"]:
        raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg="User not found")
    return response.json()["result"]
