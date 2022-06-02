import requests
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
from services.dataset import get_dataset_by_id
from services.permissions_service.decorators import dataset_permission, dataset_permission_bycode

api_ns_dataset_proxy = module_api.namespace('DatasetProxy', description='', path='/v1')
api_ns_dataset_list_proxy = module_api.namespace('DatasetProxy', description='', path='/v1')


class APIDatasetProxy(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_dataset_proxy.add_resource(self.Restful, '/dataset/<dataset_id>')
        api_ns_dataset_proxy.add_resource(self.RestfulPost, '/dataset')
        api_ns_dataset_proxy.add_resource(self.CodeRestful, '/dataset-peek/<dataset_code>')
        api_ns_dataset_list_proxy.add_resource(self.List, '/users/<username>/datasets')

    class CodeRestful(Resource):
        @jwt_required()
        @dataset_permission_bycode()
        def get(self, dataset_code):
            url = ConfigClass.DATASET_SERVICE + "dataset-peek/{}".format(dataset_code)
            respon = requests.get(url)
            return respon.json(), respon.status_code

    class Restful(Resource):
        @jwt_required()
        @dataset_permission()
        def get(self, dataset_id):
            url = ConfigClass.DATASET_SERVICE + "dataset/{}".format(dataset_id)
            respon = requests.get(url)
            return respon.json(), respon.status_code

        @jwt_required()
        @dataset_permission()
        def put(self, dataset_id):
            url = ConfigClass.DATASET_SERVICE + "dataset/{}".format(dataset_id)
            payload_json = request.get_json()
            respon = requests.put(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code

    class RestfulPost(Resource):
        @jwt_required()
        def post(self):
            url = ConfigClass.DATASET_SERVICE + "dataset"
            payload_json = request.get_json()
            operator_username = current_identity["username"]
            payload_username = payload_json.get("username")
            if operator_username != payload_username:
                return {
                    "err_msg": "No permissions: {} cannot create dataset for {}".format(
                        operator_username, payload_username)
                }, 403
            respon = requests.post(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code

    class List(Resource):
        @jwt_required()
        def post(self, username):
            url = ConfigClass.DATASET_SERVICE + "users/{}/datasets".format(username)

            # also check permission
            operator_username = current_identity["username"]
            if operator_username != username:
                return {
                    "err_msg": "No permissions"
                }, 403

            payload_json = request.get_json()
            respon = requests.post(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code


class APIDatasetFileProxy(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_dataset_proxy.add_resource(self.Restful, '/dataset/<dataset_id>/files')

    class Restful(Resource):
        @jwt_required()
        @dataset_permission()
        def get(self, dataset_id):
            url = ConfigClass.DATASET_SERVICE + "dataset/{}/files".format(dataset_id)
            respon = requests.get(url, params=request.args, headers=request.headers)
            return respon.json(), respon.status_code

        @jwt_required()
        @dataset_permission()
        def post(self, dataset_id):

            url = ConfigClass.DATASET_SERVICE + "dataset/{}/files".format(dataset_id)
            payload_json = request.get_json()
            respon = requests.post(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code

        @jwt_required()
        @dataset_permission()
        def put(self, dataset_id):
            url = ConfigClass.DATASET_SERVICE + "dataset/{}/files".format(dataset_id)
            payload_json = request.get_json()
            respon = requests.put(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code

        @jwt_required()
        @dataset_permission()
        def delete(self, dataset_id):

            url = ConfigClass.DATASET_SERVICE + "dataset/{}/files".format(dataset_id)
            payload_json = request.get_json()
            respon = requests.delete(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code


class APIDatasetFileRenameProxy(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_dataset_proxy.add_resource(self.Restful, '/dataset/<dataset_id>/files/<file_geid>')

    class Restful(Resource):
        @jwt_required()
        @dataset_permission()
        def post(self, dataset_id, file_geid):
            url = ConfigClass.DATASET_SERVICE + "dataset/{}/files/{}".format(dataset_id, file_geid)
            payload_json = request.get_json()
            respon = requests.post(url, json=payload_json, headers=request.headers)
            return respon.json(), respon.status_code


class APIDatasetFileTasks(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_dataset_proxy.add_resource(self.Restful, '/dataset/<dataset_id>/file/tasks')

    class Restful(Resource):

        @jwt_required()
        @dataset_permission()
        def get(self, dataset_id):
            request_params = request.args
            new_params = {
                **request_params,
                "label": "Dataset"
            }

            dataset = get_dataset_by_id(dataset_id)
            new_params['code'] = dataset["code"]

            url = ConfigClass.DATA_UTILITY_SERVICE + "tasks"
            response = requests.get(url, params=new_params)
            return response.json(), response.status_code

        @jwt_required()
        @dataset_permission()
        def delete(self, dataset_id):
            request_body = request.get_json()
            request_body.update({"label": "Dataset"})

            dataset = get_dataset_by_id(dataset_id)
            request_body['code'] = dataset["code"]

            url = ConfigClass.DATA_UTILITY_SERVICE + "tasks"
            response = requests.delete(url, json=request_body)
            return response.json(), response.status_code
