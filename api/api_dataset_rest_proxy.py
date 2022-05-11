from config import ConfigClass
from flask_jwt import jwt_required, current_identity
from flask_restx import Api, Resource, fields
from flask import request
from models.api_meta_class import MetaAPI
from services.permissions_service.decorators import \
    permissions_check, dataset_permission, dataset_permission_bycode
from api import module_api
import requests

api_ns_dataset_proxy = module_api.namespace('DatasetProxy', description='', path ='/v1')
api_ns_dataset_list_proxy = module_api.namespace('DatasetProxy', description='', path ='/v1')

## for backend services down/on testing
class APIDatasetProxy(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_dataset_proxy.add_resource(self.Restful, '/dataset/<dataset_geid>')
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
        def get(self, dataset_geid):
            url = ConfigClass.DATASET_SERVICE + "dataset/{}".format(dataset_geid)
            respon = requests.get(url)
            return respon.json(), respon.status_code


        @jwt_required()
        @dataset_permission()
        def put(self, dataset_geid):
            url = ConfigClass.DATASET_SERVICE + "dataset/{}".format(dataset_geid)
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
                    operator_username,payload_username)
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
        api_ns_dataset_proxy.add_resource(self.Restful, '/dataset/<dataset_geid>/files')

    class Restful(Resource):
        @jwt_required()
        @dataset_permission()
        def get(self, dataset_geid):

            url = ConfigClass.DATASET_SERVICE + "dataset/{}/files".format(dataset_geid)
            respon = requests.get(url, params=request.args, headers=request.headers, \
                cookies=request.cookies)
            return respon.json(), respon.status_code


        @jwt_required()
        @dataset_permission()
        def post(self, dataset_geid):

            url = ConfigClass.DATASET_SERVICE + "dataset/{}/files".format(dataset_geid)
            payload_json = request.get_json()
            respon = requests.post(url, json=payload_json, headers=request.headers, \
                cookies=request.cookies)
            return respon.json(), respon.status_code


        @jwt_required()
        @dataset_permission()
        def put(self, dataset_geid):
            url = ConfigClass.DATASET_SERVICE + "dataset/{}/files".format(dataset_geid)
            payload_json = request.get_json()
            respon = requests.put(url, json=payload_json, headers=request.headers, \
                cookies=request.cookies)
            return respon.json(), respon.status_code


        @jwt_required()
        @dataset_permission()
        def delete(self, dataset_geid):

            url = ConfigClass.DATASET_SERVICE + "dataset/{}/files".format(dataset_geid)
            payload_json = request.get_json()
            respon = requests.delete(url, json=payload_json, headers=request.headers, \
                cookies=request.cookies)
            return respon.json(), respon.status_code


class APIDatasetFileRenameProxy(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_dataset_proxy.add_resource(self.Restful, '/dataset/<dataset_geid>/files/<file_geid>')

    class Restful(Resource):
        @jwt_required()
        @dataset_permission()
        def post(self, dataset_geid, file_geid):

            url = ConfigClass.DATASET_SERVICE + "dataset/{}/files/{}".format(dataset_geid, file_geid)
            payload_json = request.get_json()
            respon = requests.post(url, json=payload_json, headers=request.headers, \
                cookies=request.cookies)
            return respon.json(), respon.status_code


class APIDatasetFileTasks(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_dataset_proxy.add_resource(self.Restful, '/dataset/<dataset_geid>/file/tasks')

    class Restful(Resource):

        @jwt_required()
        @dataset_permission()
        def get(self, dataset_geid):
            request_params = request.args
            new_params = {
                **request_params,
                "label": "Dataset"
            }

            relation_query_url = ConfigClass.NEO4J_SERVICE + "nodes/geid/"+dataset_geid
            response = requests.get(relation_query_url)
            new_params['code'] = response.json()[0].get("code")

            url = ConfigClass.DATA_UTILITY_SERVICE + "tasks"
            response = requests.get(url, params=new_params)
            return response.json(), response.status_code

        @jwt_required()
        @dataset_permission()
        def delete(self, dataset_geid):
            request_body = request.get_json()
            request_body.update({"label": "Dataset"})
            relation_query_url = ConfigClass.NEO4J_SERVICE + "nodes/geid/"+dataset_geid
            response = requests.get(relation_query_url)
            request_body['code'] = response.json()[0].get("code")

            url = ConfigClass.DATA_UTILITY_SERVICE + "tasks"
            response = requests.delete(url, json=request_body)
            return response.json(), response.status_code
