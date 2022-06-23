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
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from common import LoggerFactory
from services.notifier_services.email_service import SrvEmail
from services.permissions_service.decorators import PermissionsCheck
import requests
import re
from fastapi import APIRouter, Depends, Request
from fastapi_utils import cbv
from app.auth import jwt_required


router = APIRouter(tags=["Email"])


@cbv.cbv(router)
class EmailRestful:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/email',
        summary="List workbench entries",
        dependencies=[Depends(PermissionsCheck("notification", "*", "create"))]
    )
    async def post(self, request: Request):
        '''
        Send notification email to platform users
        '''
        # init logger
        _logger = LoggerFactory('api_notification').get_logger()
        response = APIResponse()

        data = await request.json()
        _logger.info("Start Notification Email: {}".format(data))
        send_to_all_active = data.get("send_to_all_active")
        emails = data.get("emails")
        subject = data.get("subject")
        message_body = data.get("message_body")

        # Check if theres something other then whitespace
        pattern = re.compile("([^\s])")
        msg_match = re.search(pattern, message_body)
        subject_match = re.search(pattern, subject)

        if not msg_match or not subject_match:
            error = "Content other then whitespace is required"
            response.set_code(EAPIResponseCode.bad_request)
            response.set_result(error)
            _logger.error(error)
            return response.to_dict

        if not subject or not message_body or not (emails or send_to_all_active):
            error = "Missing fields"
            response.set_code(EAPIResponseCode.bad_request)
            response.set_result(error)
            _logger.error(error)
            return response.to_dict

        if emails and send_to_all_active:
            error = "Can't set both emails and send_to_all_active"
            response.set_code(EAPIResponseCode.bad_request)
            response.set_result(error)
            _logger.error(error)
            return response.to_dict

        if send_to_all_active:
            payload = {"status": "active"}
            res = requests.get(ConfigClass.AUTH_SERVICE + "users", params=payload)
            users = res.json()["result"]
            emails = [i["email"] for i in users if i.get("email")]
        else:
            if not isinstance(emails, list):
                error = "emails must be list"
                response.set_result(EAPIResponseCode.bad_request)
                response.set_result(error)
                _logger.error(error)
                return response.to_dict

        email_service = SrvEmail()
        email_service.send(
            subject,
            emails,
            content=message_body,
        )

        _logger.info('Notification Email Sent')
        response.set_code(EAPIResponseCode.success)
        response.set_result('success')
        return response.to_dict
