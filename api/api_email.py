from flask_restx import Resource
from flask_jwt import jwt_required
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from models.api_meta_class import MetaAPI
from common import LoggerFactory
from services.notifier_services.email_service import SrvEmail
from services.permissions_service.decorators import permissions_check 
from api import module_api
from flask import request
import requests
import re

api_ns_notification = module_api.namespace(
    'Email Restful', description='Portal Email Restful', path='/v1')


class APIEmail(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_notification.add_resource(
            self.EmailRestful, '/email')

    class EmailRestful(Resource):
        @jwt_required()
        @permissions_check('notification', '*', 'create')
        def post(self):
            '''
            Send notification email to platform users
            '''
            # init logger
            _logger = LoggerFactory('api_notification').get_logger()
            response = APIResponse()
            access_token = request.headers.get("Authorization", None)

            data = request.get_json()
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
