from flask_restx import Api, Resource, fields
from flask_jwt import jwt_required, current_identity
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from models.api_meta_class import MetaAPI
from models.contact_us import ContactUsForm
from resources.swagger_modules import contact_us_model, contact_us_return_example
from resources.swagger_modules import read_invitation_return_example
from services.logger_services.logger_factory_service import SrvLoggerFactory
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
            '''
            This method allow to create invitation in platform.
            '''
            # init logger
            _logger = SrvLoggerFactory('api_contact_us').get_logger()
            # init resp
            my_res = APIResponse()
            # get access_token
            access_token = request.headers.get("Authorization", None)
            # init form
            post_json = request.get_json()
            _logger.info(
                "Start Creating Contact Us Email: {}".format(post_json))
            contact_form = ContactUsForm(post_json)
            # init invitation managemer
            contact_mgr = SrvContactUsManager()
            # save invitation
            contact_mgr.save_invitation(
                contact_form, access_token, current_identity)
            my_res.set_result('[SUCCEED] Invitation Saved, Email Sent')
            _logger.info('Contact Us Email Sent')
            my_res.set_code(EAPIResponseCode.success)
            return my_res.to_dict, my_res.code
