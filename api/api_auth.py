from flask_restx import Api, Resource, fields
from flask import request
import requests
from api import module_api
from models.api_meta_class import MetaAPI
from services.logger_services.logger_factory_service import SrvLoggerFactory
from services.notifier_services.email_service import SrvEmail
from services.container_services.container_manager import SrvContainerManager
from services.user_services.user_manager import SrvUserManager
from services.permissions_service.decorators import permissions_check
from models.api_response import APIResponse, EAPIResponseCode
from flask_jwt import jwt_required, current_identity
from config import ConfigClass
import jwt as pyjwt

# init logger
_logger = SrvLoggerFactory('api_auth_service').get_logger()

api_ns_auth = module_api.namespace(
    'Auth Service Restful', description='Auth Service Restful', path='/v1')


class APIAuthService(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_auth.add_resource(
            # self.AdminRestful, '/containers/<dataset_id>/users/email')
            self.AdminRestful, '/containers/users/email')
        api_ns_auth.add_resource(
            self.LastLoginRestful, '/users/lastlogin')
        api_ns_auth.add_resource(self.UserStatus, '/user/status')
        api_ns_auth.add_resource(self.UserAccount, '/user/account')

    class AdminRestful(Resource):
        @jwt_required()
        @permissions_check('users', '*', 'view')
        def get(self):
            '''
            This method allow to check email in keycloak. More information refers to auth service.
            '''
            try:
                arg = request.args
                payload = request.get_json()
                headers = request.headers
                res = requests.get(ConfigClass.AUTH_SERVICE+'admin/users/email',
                                   params=arg, json=payload, headers=headers)

                return res.json(), res.status_code
            except Exception as e:
                return {'result': str(e)}, 403

    class LastLoginRestful(Resource):
        @jwt_required()
        def post(self):
            '''
            This method allow to update user's last login time 
            '''

            try:
                payload = request.get_json()
                headers = request.headers
                res = requests.post(ConfigClass.AUTH_SERVICE+'users/lastlogin',
                                    json=payload, headers=headers)

                return res.json(), res.status_code
            except Exception as e:
                return {'result': str(e)}, 403

    class UserStatus(Resource):
        def get(self):
            '''
            Gets the users status given the email
            '''
            try:
                token = request.headers.get('Authorization')
                token = token.split()[-1]
                decoded = pyjwt.decode(token, verify=False)
                email = decoded["email"]
            except Exception as e:
                return {'result': "JWT user status error " + str(e)}, 500

            try:
                payload = {
                    "email": email
                }
                response = requests.get(
                    ConfigClass.AUTH_SERVICE + "user/status", params=payload)
                return response.json(), response.status_code
            except Exception as e:
                return {'result': "Error calling auth service" + str(e)}, 500

    class UserAccount(Resource):
        @jwt_required()
        def put(self):
            '''
            User account management
            '''
            try:
                token = request.headers.get('Authorization')
                token = token.split()[-1]
                decoded = pyjwt.decode(token, verify=False)
            except Exception as e:
                return {'result': "JWT user status error " + str(e)}, 500
            try:
                req_body = request.get_json()
                operation_type = req_body.get('operation_type', None)
                user_email = req_body.get('user_email', None)
                user_geid = req_body.get('user_geid', None)
                realm = req_body.get('realm', ConfigClass.KEYCLOAK_REALM)
                operation_payload = req_body.get('payload', {})
                # check parameters
                if not operation_type:
                    return {'result': 'operation_type required.'}, 400
                # check user identity
                if not user_email and not user_geid:
                    return {'result': 'either user_email or user_geid required.'}, 400
                # check user operation type
                if not operation_type in ['enable', 'restore', 'disable']:
                    return {'result': 'operation {} is not allowed'.format(operation_type)}, 400
                payload = {
                    "operation_type": operation_type,
                    "user_geid": user_geid,
                    "user_email": user_email,
                    "realm": realm,
                    "payload": operation_payload
                }
                headers = request.headers
                response = requests.put(
                    ConfigClass.AUTH_SERVICE + "user/account", json=payload, headers=headers)

                # send email
                user_mgr = SrvUserManager()
                user_info = user_mgr.get_user_by_email(user_email)
                if operation_type == "enable":
                    subject = "User enabled"
                    email_sender = SrvEmail()
                    email_result = email_sender.send(
                        subject,
                        [user_email],
                        msg_type="html",
                        template="user_actions/enable.html",
                        template_kwargs={
                            "username": user_info['name'],
                            "admin_name": current_identity["username"],
                            "admin_email": ConfigClass.EMAIL_ADMIN,
                            "support_email": ConfigClass.EMAIL_SUPPORT,
                        },
                    )

                    # check if platform admin
                    if user_info['role'] == 'admin':
                        _logger.info(f"User status is changed to enabled , hence creating namespace folder for : {user_info['name']}")
                        # create namespace folder for all platform admin  once enabled
                        self.create_usernamespace_folder_admin(username=user_info['name'])

                elif operation_type == "disable":
                    subject = "User disabled"
                    email_sender = SrvEmail()
                    email_result = email_sender.send(
                        subject,
                        [user_email],
                        msg_type="html",
                        template="user_actions/disable.html",
                        template_kwargs={
                            "username": user_info['name'],
                            "admin_name": current_identity["username"],
                            "admin_email": ConfigClass.EMAIL_ADMIN,
                            "support_email": ConfigClass.EMAIL_SUPPORT,
                        },
                    )
                elif operation_type == "restore":
                    project_code = operation_payload.get("project_code")
                    container_mgr = SrvContainerManager()
                    project = container_mgr.get_by_project_code(project_code)[
                        1][0]
                    subject = "Access restored to {}".format(
                        project["name"])
                    email_sender = SrvEmail()
                    email_result = email_sender.send(
                        subject,
                        [user_email],
                        msg_type="html",
                        template="user_actions/enable.html",
                        template_kwargs={
                            "username": user_info['name'],
                            "admin_name": current_identity["username"],
                            "project_name": project["name"],
                            "admin_email": ConfigClass.EMAIL_ADMIN,
                            "support_email": ConfigClass.EMAIL_SUPPORT,
                        },
                    )
                return response.json(), response.status_code
            except Exception as e:
                return {'result': "Error calling user account management service" + str(e)}, 500

        def create_usernamespace_folder_admin(self, username):
            try:
                url = ConfigClass.NEO4J_SERVICE + 'nodes/Container/query'
                res = requests.post(url, json={})
                if res.status_code == 200 and len(res.json()) > 0:
                    for project in res.json():
                        project_code = project["code"]
                        self.create_folder(folder_name=username, project_code=project_code)
            except Exception as error:
                _logger.error(f"Error while querying Container details : {error}")

        def create_folder(self, folder_name, project_code):
            try:
                _logger.info(
                    f"creating namespace folder in greenroom and core for user : {folder_name} under {project_code}")
                zone_list = ["greenroom", "core"]
                for zone in zone_list:
                    payload = {
                        "folder_name": folder_name,
                        "project_code": project_code,
                        "zone": zone,
                        "uploader": folder_name,
                        "tags": []
                    }
                    folder_creation_url = ConfigClass.DATA_UPLOAD_SERVICE_GREENROOM + '/folder'
                    res = requests.post(
                        url=folder_creation_url,
                        json=payload
                    )
                    if res.status_code == 200:
                        _logger.info(
                            f"Namespace folder created successfully for user : {folder_name} under {project_code}")
                    elif res.status_code == 409:
                        _logger.info(f"Namespace folder already exists for user : {folder_name} under {project_code}")
            except Exception as error:
                _logger.error(
                    f"Error while trying to create namespace folder for user : {folder_name} under {project_code} : {error}")
