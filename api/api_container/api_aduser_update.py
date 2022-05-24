import jwt as pyjwt
import requests
from common import LoggerFactory, ProjectClientSync
from flask import request
from flask_restx import Resource

from config import ConfigClass
from resources.error_handler import APIException
from resources.swagger_modules import new_user_module, user_sample_return

from .namespace import users_entity_ns


class ADUserUpdate(Resource):

    logger = LoggerFactory('api_aduser_update').get_logger()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @users_entity_ns.expect(new_user_module)
    @users_entity_ns.response(200, user_sample_return)
    def put(self):
        """
        This method allow user to activate the AD user account on platform.
        """
        try:
            # User is currently pending so jwt_required can't be used
            token = request.headers.get('Authorization')
            token = token.split()[-1]
            decoded = pyjwt.decode(token, verify=False)
            current_username = decoded["preferred_username"]
        except Exception as e:
            return {'result': "JWT user status error " + str(e)}, 500

        try:
            # validate payload request body
            post_data = request.get_json()
            self.logger.info('Calling API for updating AD user: {}'.format(post_data))

            email = post_data.get('email', None)
            username = post_data.get("username", None)
            first_name = post_data.get("first_name", None)
            last_name = post_data.get("last_name", None)

            if current_username != username:
                raise Exception(f"The username is not matched: {current_username}")

            if not username or not first_name or not last_name or not email:
                self.logger.error('[UserUpdateByEmail] Require field email/username/first_name/last_name.')
                return {'result': 'Required information is not sufficient.'}, 400

            # use the invitation detail to check user roles
            # and get the target project
            has_invite = True
            email = email.lower()
            filters = {"email": email, "status": "pending"}
            response = requests.post(ConfigClass.AUTH_SERVICE + "invitation-list", json={"filters": filters})
            if not response.json()["result"]:
                # Test account requests won't have an invite, they're already linked to the test projectt
                has_invite = False

            if has_invite:
                invite_detail = response.json()["result"][0]

                # The design has some implication here, if project == 'None' then
                # role means platform_role, else role means the project_role
                if invite_detail["platform_role"] == "admin":
                    self.assign_user_role_ad("platform-admin", email=email)
                    self.bulk_create_name_folder_admin(username)
                else:
                    if invite_detail["project_code"]:
                        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
                        project = project_client.get(code=invite_detail["project_code"])
                        self.assign_user_role_ad(project.code + '-' + invite_detail["project_role"], email=email)
                        self.bulk_create_folder(folder_name=username, project_code_list=[project.code])

                invite_id = invite_detail["id"]
                response = requests.put(
                    ConfigClass.AUTH_SERVICE + f"invitation/{invite_id}",
                    json={"status": "complete"}
                )
                invite_detail = response.json()

            # update status/login
            return self.update_user_status(email)
        except Exception as error:
            self.logger.error(f"Error when updating user data : {error}")

            return {"result": {}, "error_msg": str(error)}

    def update_user_status(self, email):
        payload = {
            "operation_type": "enable",
            "user_email": email,
        }
        response = requests.put(ConfigClass.AUTH_SERVICE + "user/account", json=payload)
        self.logger.info('Update user in auth results: %s', response.json())
        if response.status_code != 200:
            self.logger.info('Done with updating user node to neo4j')
            raise (Exception('Internal error when updating user data'))
        return {"result": response.json()}, 200

    def assign_user_role_ad(self, role: str, email):
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

    def bulk_create_folder(self, folder_name: str, project_code_list: list):
        try:
            self.logger.info(f"bulk creating namespace folder in greenroom \
                    and core for user : {folder_name} under {project_code_list}")
            zone_list = [ConfigClass.GREENROOM_ZONE_LABEL, ConfigClass.CORE_ZONE_LABEL]

            folders = []
            # since api is accept the zone independent with
            for zone in zone_list:
                for project_code in project_code_list:
                    folders.append({
                        "name": folder_name,
                        "zone": 0 if zone == "greenroom" else 1,
                        "type": "name_folder",
                        "owner": folder_name,
                        "container_code": project_code,
                        "container_type": "project",
                        "size": 0,
                        "location_uri": "",
                        "version": "",
                    })
            response = requests.post(ConfigClass.METADATA_SERVICE + "items/batch/", json=folders)
            if response.status_code == 200:
                self.logger.info(f"In namespace: {zone}, folders bulk created successfully for user: {folder_name} \
                        under {project_code_list}")
        except Exception as error:
            self.logger.error(
                f"Error while trying to create namespace folder for user : {folder_name} under {project_code_list} : \
                        {error}")
            raise error

    def bulk_create_name_folder_admin(self, username):
        try:
            project_code_list = []
            project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
            project_result = project_client.search()
            projects = project_result["result"]
            for project in projects:
                project_code_list.append(project.code)
            self.bulk_create_folder(folder_name=username, project_code_list=project_code_list)
            return False
        except Exception as error:
            self.logger.error(f"Error while querying Container details : {error}")
