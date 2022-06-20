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
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from models.api_meta_class import MetaAPI
from models.contact_us import ContactUsForm
from resources.swagger_modules import contact_us_model, contact_us_return_example
from resources.swagger_modules import read_invitation_return_example
from common import LoggerFactory
from services.contact_us_services.contact_us_manager import SrvContactUsManager
from api import module_api
from flask import request
import json

api_ns_contact = module_api.namespace(
    'Contact Us Restful', description='Portal Contact Us Restful', path='/v1')


class APIContactUs(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_contact.add_resource(
            self.ContactUsRestful, '/contact')

    class ContactUsRestful(Resource):
        @api_ns_contact.expect(contact_us_model)
        @api_ns_contact.response(200, contact_us_return_example)
        def post(self):
            _logger = LoggerFactory('api_contact_us').get_logger()
            my_res = APIResponse()
            access_token = request.headers.get("Authorization", None)
            post_json = request.get_json()
            _logger.info("Start Creating Contact Us Email: {}".format(post_json))
            contact_form = ContactUsForm(post_json)
            contact_mgr = SrvContactUsManager()
            contact_mgr.save_invitation(contact_form, access_token, current_identity)
            my_res.set_result('[SUCCEED] Contact us Email Sent')
            _logger.info('Contact Us Email Sent')
            my_res.set_code(EAPIResponseCode.success)
            return my_res.to_dict, my_res.code
