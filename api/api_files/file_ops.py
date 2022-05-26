import requests
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource

from config import ConfigClass
from models.api_response import EAPIResponseCode
from resources.error_handler import APIException
from common import LoggerFactory, ProjectClientSync
from services.permissions_service.decorators import permissions_check
from services.permissions_service.utils import get_project_role, has_permission
from services.meta import get_entity_by_id

_logger = LoggerFactory('api_files_ops_v1').get_logger()


# by default this proxy will ONLY call
# the Container related apis.
class FileActionTasks(Resource):
    @jwt_required()
    @permissions_check('tasks', '*', 'view')
    def get(self):
        request_params = {**request.args}
        # here update the project_code to code
        request_params.update({"code": request_params.get("project_code")})
        url = ConfigClass.DATA_UTILITY_SERVICE + "tasks"
        response = requests.get(url, params=request_params)
        if response.status_code == 200:
            return response.json(), response.status_code
        else:
            return response.text, 500

    @jwt_required()
    @permissions_check('tasks', '*', 'delete')
    def delete(self):
        request_body = request.get_json()
        url = ConfigClass.DATA_UTILITY_SERVICE + "tasks"
        response = requests.delete(url, json=request_body)
        if response.status_code == 200:
            return response.json(), response.status_code
        else:
            return response.text, 500


class FileActions(Resource):
    @jwt_required()
    def post(self):
        data_actions_utility_url = ConfigClass.DATA_UTILITY_SERVICE + "files/actions/"
        headers = request.headers
        request_body = request.get_json()
        validate_request_params(request_body)
        operation = request_body.get("operation", None)
        project_geid = request_body.get("project_geid", None)
        targets = request_body["payload"]["targets"]
        # validate request
        session_id = headers.get("Session-Id", None)
        if not session_id:
            return "Header Session-ID required", EAPIResponseCode.bad_request.value

        project_info = get_project_or_error(project_geid)

        if not has_permission(project_info["code"], 'file', '*', operation.lower()):
            return "Permission denied", EAPIResponseCode.forbidden.value

        if operation == 'delete':
            validate_delete_permissions(targets, project_info["code"])

        # request action utility API
        payload = request_body
        payload['session_id'] = session_id
        action_util_res = requests.post(data_actions_utility_url, json=payload, headers=request.headers)
        if action_util_res.status_code == 202:
            return action_util_res.json(), action_util_res.status_code
        else:
            return action_util_res.text, action_util_res.status_code


class FileRepeatedCheck(Resource):
    @jwt_required()
    def post(self):
        data_actions_utility_url = ConfigClass.DATA_UTILITY_SERVICE + "files/actions/validate/repeat-check"
        headers = request.headers
        request_body = request.get_json()
        validate_request_params(request_body)
        operation = request_body.get("operation", None)
        project_geid = request_body.get("project_geid", None)
        targets = request_body["payload"]["targets"]
        session_id = headers.get("Session-ID", None)
        if not session_id:
            return "Header Session-ID required", EAPIResponseCode.bad_request.value

        # validate project
        project_info = get_project_or_error(project_geid)

        if not has_permission(project_info["code"], 'file', '*', operation.lower()):
            return "Permission denied", EAPIResponseCode.forbidden.value

        if operation == "delete":
            validate_delete_permissions(targets, project_info["code"])

        # request action utility API
        payload = request_body
        payload['session_id'] = session_id
        action_util_res = requests.post(data_actions_utility_url, json=payload)
        if action_util_res.status_code == 200:
            return action_util_res.json(), action_util_res.status_code
        else:
            return action_util_res.text, action_util_res.status_code


class FileValidation(Resource):
    @jwt_required()
    def post(self):
        try:
            data_actions_utility_url = ConfigClass.DATA_UTILITY_SERVICE + "files/actions/validate"
            request_body = request.get_json()
            validate_request_params(request_body)
            operation = request_body.get("operation", None)
            project_geid = request_body.get("project_geid", None)
            targets = request_body["payload"]["targets"]

            project_info = get_project_or_error(project_geid)
            _logger.info('file validation api: project info' + str(project_info))

            if not has_permission(project_info["code"], 'file', '*', operation.lower()):
                return "Permission denied", EAPIResponseCode.forbidden.value

            if operation == 'delete':
                validate_delete_permissions(targets, project_info["code"])

            # request action utility API
            payload = request_body
            _logger.error('file validation api call utility service: ' + str(payload))
            action_util_res = requests.post(data_actions_utility_url, json=payload)
            return action_util_res.json(), action_util_res.status_code
        except Exception as e:
            _logger.error('file validation error: ' + str(e))
            return "file validation error: " + str(e), EAPIResponseCode.internal_error.value


def validate_request_params(request_body: dict):
    if not request_body.get("payload"):
        raise APIException(error_msg="parameter 'payload' required", status_code=EAPIResponseCode.bad_request.value)

    targets = request_body["payload"].get("targets")
    if not targets:
        raise APIException(error_msg="targets required", status_code=EAPIResponseCode.bad_request.value)
    if type(targets) != list:
        raise APIException(error_msg="Invalid targets, must be an object list", status_code=EAPIResponseCode.bad_request.value)
    if not request_body.get("operation"):
        raise APIException(error_msg="operation required", status_code=EAPIResponseCode.bad_request.value)
    if not request_body.get("project_geid"):
        raise APIException(error_msg="project_geid required", status_code=EAPIResponseCode.bad_request.value)


def get_project_or_error(project_geid: str) -> dict:
    project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
    project = project_client.get(id=project_geid)
    return project.json()


def validate_delete_permissions(targets: list, project_code):
    '''
        Project admin can delete files
        Project collaborator can only delete the file belong to them
        Project contributor can only delete the greenroom file belong to them (confirm the file is greenroom file, and has owned by current user)
    '''
    user_project_role = get_project_role(project_code)
    if user_project_role not in ["admin", "platform-admin"]:
        for target in targets:
            source = get_entity_by_id(target['geid'])
            zone = "greenroom" if source["zone"] == 1 else "core"

            if user_project_role == 'contributor':
                root_folder = source["parent_path"].split("/")[0]
                if root_folder != current_identity['username']:
                    error_msg = "Permission denied on file: " + source['id']
                    raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.forbidden.value)
                if zone == "core":
                    error_msg = "Permission denied on file: " + source['id']
                    raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.forbidden.value)
            if user_project_role == 'collaborator':
                if zone == "greenroom":
                    root_folder = source["parent_path"].split(".")[0]
                    if root_folder != current_identity['username']:
                        error_msg = "Permission denied on file: " + source['id']
                        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.forbidden.value)
