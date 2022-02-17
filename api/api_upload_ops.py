# # from config import ConfigClass
# # from .proxy import BaseProxyResource


# # class CheckUploadStateRestful(BaseProxyResource):
# #     methods = ["DELETE"]
# #     required_roles = {"DELETE": "uploader"}
# #     url = ConfigClass.DATA_UTILITY_SERVICE + "files/upload-state"


from email import header
from config import ConfigClass
from flask_jwt import jwt_required, current_identity
from flask_restx import Api, Resource, fields
from flask import request
from models.api_meta_class import MetaAPI
from api import module_api
import requests

api_uplaod = module_api.namespace('UploadStatusProxy', description='', path ='/v1')


class APIFileUploadStatus(metaclass=MetaAPI):
    def api_registry(self):
        api_uplaod.add_resource(self.FileUploadStatus, '/upload/containers/<project_geid>/upload-state')
        
    class FileUploadStatus(Resource):
        @jwt_required()
        def delete(self, project_geid):
            url = ConfigClass.DATA_UTILITY_SERVICE + "files/upload-state"
            respon = requests.delete(url, params=request.args, headers=request.headers, \
                cookies=request.cookies)
            return respon.json(), respon.status_code


