from config import ConfigClass
from flask_jwt import jwt_required
from flask_restx import Resource
from flask import request
from models.api_meta_class import MetaAPI
from services.permissions_service.decorators import dataset_permission
from api import module_api
import requests

api_ns_dataset_schema_template_proxy = module_api.namespace('DatasetSchemaTemplateProxy', description='', path='/v1')


class APIDatasetSchemaTemplateProxy(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_dataset_schema_template_proxy.add_resource(
            self.Restful, '/dataset/<dataset_id>/schemaTPL/<template_geid>'
        )
        api_ns_dataset_schema_template_proxy.add_resource(
            self.SchemaTemplateCreate, '/dataset/<dataset_id>/schemaTPL'
        )
        api_ns_dataset_schema_template_proxy.add_resource(
            self.SchemaTemplatePostQuery, '/dataset/<dataset_id>/schemaTPL/list'
        )
        api_ns_dataset_schema_template_proxy.add_resource(
            self.SchemaTemplateDefaultQuery, '/dataset/schemaTPL/default/list'
        )
        api_ns_dataset_schema_template_proxy.add_resource(
            self.SchemaTemplateDefaultGet, '/dataset/schemaTPL/default/<template_geid>'
        )

    class Restful(Resource):
        @jwt_required()
        @dataset_permission()
        def get(self, dataset_id, template_geid):
            url = ConfigClass.DATASET_SERVICE + "dataset/{}/schemaTPL/{}".format(dataset_id, template_geid)
            respon = requests.get(url, params=request.args, headers=request.headers)
            return respon.json(), respon.status_code

        @jwt_required()
        @dataset_permission()
        def put(self, dataset_id, template_geid):
            url = ConfigClass.DATASET_SERVICE + "dataset/{}/schemaTPL/{}".format(dataset_id, template_geid)
            payload_json = request.get_json()
            respon = requests.put(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code

        @jwt_required()
        @dataset_permission()
        def delete(self, dataset_id, template_geid):
            url = ConfigClass.DATASET_SERVICE + "dataset/{}/schemaTPL/{}".format(dataset_id, template_geid)
            payload_json = request.get_json()
            respon = requests.delete(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code

    class SchemaTemplateCreate(Resource):
        @jwt_required()
        @dataset_permission()
        def post(self, dataset_id):
            url = ConfigClass.DATASET_SERVICE + "dataset/{}/schemaTPL".format(dataset_id)
            payload_json = request.get_json()
            respon = requests.post(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code

    class SchemaTemplatePostQuery(Resource):
        @jwt_required()
        @dataset_permission()
        def post(self, dataset_id):
            url = ConfigClass.DATASET_SERVICE + "dataset/{}/schemaTPL/list".format(dataset_id)
            payload_json = request.get_json()
            respon = requests.post(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code

###################################################################################################

    # note this api will have different policy
    class SchemaTemplateDefaultQuery(Resource):
        @jwt_required()
        def post(self):
            url = ConfigClass.DATASET_SERVICE + "dataset/default/schemaTPL/list"
            payload_json = request.get_json()
            respon = requests.post(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code

    class SchemaTemplateDefaultGet(Resource):
        @jwt_required()
        def get(self, template_geid):
            url = ConfigClass.DATASET_SERVICE + "dataset/default/schemaTPL/{}".format(template_geid)
            respon = requests.get(url, params=request.args, headers=request.headers)
            return respon.json(), respon.status_code
