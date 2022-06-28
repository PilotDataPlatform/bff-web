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
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from app.auth import jwt_required
import math

from models.api_response import APIResponse, EAPIResponseCode
from config import ConfigClass
from services.notifier_services.email_service import SrvEmail
from common import LoggerFactory, ProjectClient
from services.permissions_service.decorators import PermissionsCheck
from resources.error_handler import APIException


_logger = LoggerFactory('api_resource_request').get_logger()
router = APIRouter(tags=["Resource Request"])


@cbv.cbv(router)
class ResourceRequest:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/resource-request/{request_id}/',
        summary="Get a single resource request",
        dependencies=[Depends(PermissionsCheck("resource_request", "*", "view"))]
    )
    async def get(self, request_id: str):
        """
         Get a single resource request
        """
        api_response = APIResponse()
        _logger.info("ResourceRequest get called")

        if self.current_identity["role"] != "admin":
            api_response.set_error_msg("Permissions denied")
            api_response.set_code(EAPIResponseCode.forbidden)
            return api_response.json_response()

        try:
            # TODO call resource request API
            pass
        except Exception as e:
            _logger.error("Error calling resource request API: " + str(e))
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result("Psql Error: " + str(e))
            return api_response.json_response()
        api_response.set_result("")
        return api_response.json_response()

    @router.delete(
        '/resource-request/{request_id}/',
        summary="Delete a single resource request",
        dependencies=[Depends(PermissionsCheck("resource_request", "*", "delete"))]
    )
    async def delete(self, request_id: str):
        api_response = APIResponse()
        _logger.info("ResourceRequest get called")

        try:
            # TODO call resource request API
            pass
        except Exception as e:
            _logger.error("Error calling resource request API: " + str(e))
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result("Psql Error: " + str(e))
            return api_response.json_response()
        api_response.set_result('success')
        return api_response.json_response()


@cbv.cbv(router)
class ResourceRequestComplete:
    current_identity: dict = Depends(jwt_required)

    @router.put(
        '/resource-request/{request_id}/complete',
        summary="Update an existing resource request as complete",
        dependencies=[Depends(PermissionsCheck("resource_request", "*", "update"))]
    )
    async def put(self, request_id: str):
        """
            Update an existing resource request as complete
        """
        api_response = APIResponse()
        _logger.info("ResourceRequestComplete put called")

        try:
            # TODO call resource request API
            resource_request = {}
            pass
        except Exception as e:
            _logger.error("Error calling resource request API: " + str(e))
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result("Psql Error: " + str(e))
            return api_response.json_response()

        project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = await project_client.get(id=resource_request.project_geid)

        template_kwargs = {
            "current_user": self.current_identity["username"],
            "request_for": resource_request.request_for,
            "project_name": resource_request.project_name,
            "project_code": project.code,
            "admin_email": ConfigClass.EMAIL_SUPPORT,
        }
        try:
            email_sender = SrvEmail()
            email_sender.send(
                f"Access granted to {resource_request.request_for}",
                [resource_request.email],
                msg_type='html',
                template="resource_request/approved.html",
                template_kwargs=template_kwargs,
            )
            _logger.info(f"Email sent to {resource_request.email}")
        except Exception as e:
            _logger.error("Error sending email: " + str(e))
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result("Error sending email: " + str(e))
            return api_response.json_response()

        api_response.set_result("")
        return api_response.json_response()


@cbv.cbv(router)
class ResourceRequestsQuery:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/resource-requests/query',
        summary="List resource requests",
    )
    async def post(self, request: Request):
        """
            List resource requests
        """
        _logger.info("ResourceRequestsQuery post called")
        api_response = APIResponse()
        data = await request.json()

        page = int(data.get('page', 0))
        # use 0 start for consitency with other pagination systems
        page = page + 1
        page_size = int(data.get('page_size', 25))
        order_by = data.get('order_by', "request_date")
        order_type = data.get('order_type', "asc")
        filters = data.get('filters', {})

        try:
            if self.current_identity["role"] != "admin":
                filters["username"] = self.current_identity["username"]

            # TODO add resource request call
        except Exception as e:
            _logger.error("Psql error: " + str(e))
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result("Psql error: " + str(e))
            return api_response.json_response()

        total = 0
        api_response.set_page(page - 1)
        api_response.set_num_of_pages(math.ceil(total / page_size))
        api_response.set_total(total)
        api_response.set_result([])
        return api_response.json_response()


@cbv.cbv(router)
class ResourceRequests:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/resource-requests',
        summary="Create a new resource request, send email notification",
        dependencies=[Depends(PermissionsCheck("resource_request", "*", "create"))]
    )
    async def post(self, request: Request):

        """
            Create a new resource request, send email notification
        """
        _logger.info("ResourceRequests post called")
        api_response = APIResponse()
        data = await request.json()
        try:
            # validate payload
            is_valid, res, code = validate_payload(data)
            if not is_valid:
                return res, code
            else:
                model_data = res

            #duplicate_check(data)

            # get user node
            #user_node = get_user_node(data["user_id"])

            project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
            project = await project_client.get(id=data["project_geid"])

            model_data["username"] = self.current_identity["username"]
            model_data["email"] = self.current_identity["email"]
            model_data["project_name"] = project.name

            user_role = None
            for role in get_realm_roles(self.current_identity["username"]):
                if role["name"].split("-")[0] == project.code:
                    user_role = role["name"].split("-")[-1]
                    break

            # TODO call resource request API
            resource_request = {}

            # send_email
            is_email_sent, email_res, code = send_email(resource_request, project, user_role)
            if not is_email_sent:
                return email_res, code
            api_response.set_result(resource_request.to_dict())
            return api_response.json_response()

        except Exception as e:
            raise e
            _logger.error("Psql error: " + str(e))
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result("Psql error: " + str(e))
            return api_response.json_response()


def validate_payload(data):
    api_response = APIResponse()
    model_data = {}
    required_fields = ["user_id", "project_geid", "request_for"]
    for field in required_fields:
        if field in data:
            model_data[field] = data[field]
            continue
        api_response.set_code(EAPIResponseCode.bad_request)
        api_response.set_result(f"Missing required field {field}")
        return False, api_response.to_dict, api_response.code
    if not data["request_for"] in ConfigClass.RESOURCES:
        api_response.set_code(EAPIResponseCode.bad_request)
        api_response.set_result("Invalid request_for field")
        return False, api_response.to_dict, api_response.code
    return True, model_data, 200


def get_realm_roles(username: str) -> list:
    payload = {
        "username": username,
    }
    response = requests.get(ConfigClass.AUTH_SERVICE + "admin/users/realm-roles", params=payload)
    if not response.json():
        raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg="User not found in keycloak")
    return response.json()["result"]


def send_email(resource_request, project, user_role):
    api_response = APIResponse()
    template_kwargs = {
        "username": resource_request.username,
        "request_for": resource_request.request_for,
        "project_name": resource_request.project_name,
        "project_code": project.code,
        "admin_email": ConfigClass.EMAIL_SUPPORT,
        "portal_url": ConfigClass.SITE_DOMAIN,
        "user_role": user_role.title()
    }
    try:
        query = {"username": ConfigClass.RESOURCE_REQUEST_ADMIN}
        response = requests.get(ConfigClass.AUTH_SERVICE + "admin/user", params=query)
        admin_email = response.json()["result"]["email"]
    except Exception as e:
        _logger.error("Error getting admin email: " + str(e))
        api_response.set_code(EAPIResponseCode.internal_error)
        api_response.set_result("Error getting admin email: " + str(e))
        return False, api_response.to_dict, api_response.code

    try:
        email_sender = SrvEmail()
        email_sender.send(
            "Resource Request from " + template_kwargs["username"],
            [admin_email],
            msg_type='html',
            template="resource_request/request.html",
            template_kwargs=template_kwargs,
        )
        _logger.info(f"Email sent to {admin_email}")
        return True, None, 200
    except Exception as e:
        _logger.error("Error sending email: " + str(e))
        api_response.set_code(EAPIResponseCode.internal_error)
        api_response.set_result("Error sending email: " + str(e))
        return False, api_response.to_dict, api_response.code
