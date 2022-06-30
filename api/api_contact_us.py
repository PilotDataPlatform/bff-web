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
from common import LoggerFactory
from fastapi import APIRouter, Request
from fastapi_utils import cbv

from models.api_response import APIResponse, EAPIResponseCode
from models.contact_us import ContactUsForm
from services.contact_us_services.contact_us_manager import SrvContactUsManager

router = APIRouter(tags=["Contact Us"])


@cbv.cbv(router)
class ContactUsRestful:

    @router.post(
        '/contact',
        summary="Sends a contact us message",
    )
    def post(self, request: Request):
        _logger = LoggerFactory('api_contact_us').get_logger()
        my_res = APIResponse()
        post_json = request.json()
        _logger.info("Start Creating Contact Us Email: {}".format(post_json))
        contact_form = ContactUsForm(post_json)
        contact_mgr = SrvContactUsManager()
        contact_mgr.send_contact_us_email(contact_form)
        my_res.set_result('[SUCCEED] Contact us Email Sent')
        _logger.info('Contact Us Email Sent')
        my_res.set_code(EAPIResponseCode.success)
        return my_res.json_response()
