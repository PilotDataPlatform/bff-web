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
import jwt as pyjwt
import requests
from common import LoggerFactory, ProjectClient
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from config import ConfigClass
from models.api_response import EAPIResponseCode
from resources.error_handler import APIException
from services.notifier_services.email_service import SrvEmail

# init logger
_logger = LoggerFactory('api_auth_service').get_logger()

router = APIRouter(tags=["Auth"])


@cbv.cbv(router)
class LastLoginRestful:
    current_identity: dict = Depends(jwt_required)

    @router.put(
        '/users/lastlogin',
        summary="Update user's last login time",
    )
    async def put(self, request: Request):
        try:
            payload = await request.json()
            # the auth api will format the last_login as "%Y-%m-%dT%H:%M:%S"
            payload.update({"last_login": True})
            res = requests.put(ConfigClass.AUTH_SERVICE + 'admin/user', json=payload)
            return JSONResponse(content=res.json(), status_code=res.status_code)
        except Exception as e:
            return JSONResponse(content={'result': str(e)}, status_code=403)


@cbv.cbv(router)
class UserStatus:
    @router.get(
        '/user/status',
        summary="Get users status given the email",
    )
    def get(self, request: Request):
        try:
            token = request.headers.get('Authorization')
            token = token.split()[-1]
            decoded = pyjwt.decode(token, verify=False)
            email = decoded["email"]
        except Exception as e:
            return JSONResponse(content={'result': "JWT user status error " + str(e)}, status_code=500)

        try:
            payload = {"email": email}
            response = requests.get(ConfigClass.AUTH_SERVICE + "admin/user", params=payload)
            if not response.json()["result"]:
                return JSONResponse(content="User not found", status_code=404)
            status = response.json()["result"]["attributes"]["status"]
            response_json = response.json()
            result = {
                "email": email,
                "status": status,
            }
            response_json["result"] = result
            return JSONResponse(content=response_json, status_code=response.status_code)
        except Exception as e:
            return JSONResponse(content={'result': "Error calling auth service" + str(e)}, status_code=500)


@cbv.cbv(router)
class UserAccount:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/user/account',
        summary="user account mangaement",
    )
    async def put(self, request: Request):
        try:
            req_body = await request.json()
            operation_type = req_body.get('operation_type', None)
            user_email = req_body.get('user_email', None)
            user_id = req_body.get('user_id', None)
            realm = req_body.get('realm', ConfigClass.KEYCLOAK_REALM)
            operation_payload = req_body.get('payload', {})
            # check parameters
            if not operation_type:
                return JSONResponse(
                    content={'result': 'operation_type required.'},
                    status_code=400
                )
            # check user identity
            if not user_email and not user_id:
                return JSONResponse(
                    content={'result': 'either user_email or user_id required.'},
                    status_code=400
                )
            # check user operation type
            if operation_type not in ['enable', 'disable']:
                return JSONResponse(
                    content={'result': 'operation {} is not allowed'.format(operation_type)},
                    status_code=400
                )
            payload = {
                "operation_type": operation_type,
                "user_id": user_id,
                "user_email": user_email,
                "realm": realm,
                "payload": operation_payload,
                "operator": self.current_identity["username"],
            }
            headers = request.headers
            response = requests.put(ConfigClass.AUTH_SERVICE + "user/account", json=payload, headers=headers)

            # send email
            payload = {"email": user_email}
            response = requests.get(ConfigClass.AUTH_SERVICE + "admin/user", params=payload)
            user_info = response.json()["result"]
            if operation_type == "enable":
                subject = "User enabled"
                email_sender = SrvEmail()
                email_sender.send(
                    subject,
                    [user_email],
                    msg_type="html",
                    template="user_actions/enable.html",
                    template_kwargs={
                        "username": user_info.get("username"),
                        "admin_name": self.current_identity["username"],
                        "admin_email": ConfigClass.EMAIL_ADMIN,
                        "support_email": ConfigClass.EMAIL_SUPPORT,
                    },
                )

                # check if platform admin
                if user_info['role'] == 'admin':
                    _logger.info(
                        "User status is changed to enabled , hence creating namespace folder for: %s"
                        % (user_info.get("username"))
                    )
                    # create namespace folder for all platform admin  once enabled
                    await self.create_usernamespace_folder_admin(username=user_info.get("username"))

            elif operation_type == "disable":
                subject = "User disabled"
                email_sender = SrvEmail()
                email_sender.send(
                    subject,
                    [user_email],
                    msg_type="html",
                    template="user_actions/disable.html",
                    template_kwargs={
                        "username": user_info.get("username"),
                        "admin_name": self.current_identity["username"],
                        "admin_email": ConfigClass.EMAIL_ADMIN,
                        "support_email": ConfigClass.EMAIL_SUPPORT,
                    },
                )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            return JSONResponse(
                content={'result': "Error calling user account management service" + str(e)},
                status_code=500
            )

    async def create_usernamespace_folder_admin(self, username):
        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        page = 0
        result = await project_client.search(page=page, page_size=50)
        projects = result["result"]
        while projects:
            result = await project_client.search(page=page, page_size=50)
            projects = result["result"]
            project_codes = [i.code for i in projects]
            page += 1
            self.bulk_create_folder_usernamespace(username, project_codes)

    def bulk_create_folder_usernamespace(self, username: str, project_codes: list):
        try:
            zone_list = ["greenroom", "core"]
            folders = []
            for zone in zone_list:
                for project_code in project_codes:
                    folders.append({
                        "name": username,
                        "zone": 0 if zone == "greenroom" else 1,
                        "type": "name_folder",
                        "owner": username,
                        "container_code": project_code,
                        "container_type": "project",
                        "size": 0,
                        "location_uri": "",
                        "version": "",
                    })

            payload = {"items": folders, "skip_duplicates": True}
            res = requests.post(ConfigClass.METADATA_SERVICE + 'items/batch/', json=payload)
            if res.status_code != 200:
                raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=res.json())

        except Exception as e:
            error_msg = f"Error while trying to bulk create namespace folder, error: {e}"
            _logger.error(error_msg)
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
