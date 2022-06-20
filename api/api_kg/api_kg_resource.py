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
        @jwt_required()
        def post(self):
            url = ConfigClass.KG_SERVICE + "resources"
            payload_json = request.get_json()
            respon = requests.post(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code
