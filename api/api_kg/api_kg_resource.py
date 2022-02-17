from config import ConfigClass
from flask_jwt import jwt_required, current_identity
from flask_restx import Api, Resource, fields
from flask import request
from models.api_meta_class import MetaAPI
from api import module_api
import requests

api_ns_kg_resource_proxy = module_api.namespace('KGResourceProxy', description='', path ='/v1')

## for backend services down/on testing
class APIKGResourceProxy(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_kg_resource_proxy.add_resource(self.KGResource, '/kg/resources')


    class KGResource(Resource):
        # @jwt_required()
        def post(self):
            url = ConfigClass.KG_SERVICE + "resources"
            payload_json = request.get_json()
            respon = requests.post(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code
