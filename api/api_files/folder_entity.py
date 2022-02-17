from .proxy import BaseProxyResource
from config import ConfigClass
from flask_restx import Resource
from flask_jwt import jwt_required
from services.permissions_service.decorators import permissions_check
import requests


class FoldersEntity(Resource):
    url = ConfigClass.ENTITYINFO_SERVICE + "folders"
    @jwt_required()
    @permissions_check("file", "*", "view")
    def get(self):
        response = requests.get(self.url, params=request.args)
        return response.json(), response.status_code

    @jwt_required()
    @permissions_check("file", "*", "create")
    def post(self):
        response = requests.post(self.url, json=request.get_json())
        return response.json(), response.status_code
    

# depracated
class FolderEntity(BaseProxyResource):
    methods = ["GET", "POST"]
    required_roles = {"GET": "member", "POST": "member"}
    url = ConfigClass.ENTITYINFO_SERVICE + "folder/{geid}"
