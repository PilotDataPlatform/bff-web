from flask import request
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from ..api_files.proxy import BaseProxyResource
from models.api_response import APIResponse, EAPIResponseCode
from services.logger_services.logger_factory_service import SrvLoggerFactory
from models.api_meta_class import MetaAPI
from config import ConfigClass
from resources.utils import http_query_node, get_relation
import json
import requests
from api import module_api
from services.permissions_service.decorators import permissions_check

_logger = SrvLoggerFactory('api_dataset_validator').get_logger()

api_dataset = module_api.namespace(
    'Dataset BIDS Validator', description='Dataset BIDS Validator API', path='/v1/dataset')


class APIValidator(metaclass=MetaAPI):
    def api_registry(self):
        api_dataset.add_resource(
            self.BIDSValidator, '/bids-validate')
        api_dataset.add_resource(
            self.BIDSResult, '/bids-validate/<dataset_geid>')

    class BIDSValidator(Resource):
        @jwt_required()
        def post(self):
            _res = APIResponse()
            payload = request.get_json()
            dataset_geid = payload.get('dataset_geid', None)
            if not dataset_geid:
                _res.code = EAPIResponseCode.bad_request
                _res.error_msg = "dataset_geid is missing in payload"
                return _res.to_dict, _res.code

            _logger.info(
                f'Call API for validating dataset: {dataset_geid}')

            try:
                node_res = http_query_node(
                    'Dataset', {'global_entity_id': dataset_geid})
                node = node_res.json()
                if len(node) == 0:
                    _res.set_code(EAPIResponseCode.not_found)
                    _res.set_result('Dataset is not exist')
                    return _res.to_dict, _res.code
                if node[0]['type'] != 'BIDS':
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result('Dataset is not BIDS type')
                    return _res.to_dict, _res.code

                relations = get_relation('User', 'Dataset', {
                                         "name": current_identity['username']}, {"id": node[0]['id']})
                if len(relations) == 0:
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_result("no permission for this dataset")
                    return _res.to_dict, _res.code
            except Exception as e:
                _res.code = EAPIResponseCode.bad_request
                _res.error_msg = "error when get dataset node in neo4j" + \
                    str(e)
                return _res.to_dict, _res.code

            try:
                url = ConfigClass.DATASET_SERVICE + 'dataset/verify/pre'
                data = {
                    "dataset_geid": dataset_geid,
                    "type": "bids"
                }
                response = requests.post(
                    url, headers=request.headers, json=data)
                if response.status_code != 200:
                    _logger.error(
                        'Failed to verify dataset in dataset service:   ' + response.text)
                    _res.set_code(EAPIResponseCode.internal_error)
                    _res.set_result(
                        'Failed to verify dataset in dataset service:   ' + response.text)
                    return _res.to_dict, _res.code
                else:
                    return response.json()

            except Exception as e:
                _res.code = EAPIResponseCode.bad_request
                _res.error_msg = "error when verify dataset in service dataset" + \
                    str(e)
                return _res.to_dict, _res.code

    class BIDSResult(Resource):
        @jwt_required()
        def get(self, dataset_geid):
            _res = APIResponse()

            try:
                node_res = http_query_node(
                    'Dataset', {'global_entity_id': dataset_geid})
                node = node_res.json()
                if len(node) == 0:
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result('Dataset is not exist')
                    return _res.to_dict, _res.code

                relations = get_relation('User', 'Dataset', {
                                         "name": current_identity['username']}, {"id": node[0]['id']})
                if len(relations) == 0:
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_result("no permission for this dataset")
                    return _res.to_dict, _res.code
            except Exception as e:
                _res.code = EAPIResponseCode.bad_request
                _res.error_msg = "error when get dataset node in neo4j" + \
                    str(e)
                return _res.to_dict, _res.code

            try:
                url = ConfigClass.DATASET_SERVICE + \
                    'dataset/bids-msg/{}'.format(dataset_geid)
                response = requests.get(url)
                if response.status_code != 200:
                    _logger.error(
                        'Failed to get dataset bids result in dataset service:   ' + response.text)
                    _res.set_code(EAPIResponseCode.internal_error)
                    _res.set_result(
                        'Failed to get dataset bids result in dataset service:   ' + response.text)
                    return _res.to_dict, _res.code
                else:
                    return response.json()

            except Exception as e:
                _res.code = EAPIResponseCode.bad_request
                _res.error_msg = "error when get dataset bids result in service dataset" + \
                    str(e)
                return _res.to_dict, _res.code
