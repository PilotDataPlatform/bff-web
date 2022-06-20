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
import requests
from common import LoggerFactory
from flask import request
from flask_jwt import current_identity
from flask_jwt import jwt_required
from flask_restx import Resource

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.dataset import get_dataset_by_id

_logger = LoggerFactory('api_dataset_validator').get_logger()

api_dataset = module_api.namespace(
    'Dataset BIDS Validator', description='Dataset BIDS Validator API', path='/v1/dataset')


class APIValidator(metaclass=MetaAPI):
    def api_registry(self):
        api_dataset.add_resource(self.BIDSValidator, '/bids-validate')
        api_dataset.add_resource(self.BIDSResult, '/bids-validate/<dataset_id>')

    class BIDSValidator(Resource):
        @jwt_required()
        def post(self):
            _res = APIResponse()
            payload = request.get_json()
            dataset_id = payload.get('dataset_geid', None)
            if not dataset_id:
                _res.set_code(EAPIResponseCode.bad_request)
                _res.set_error_msg('dataset_id is missing in payload')
                return _res.to_dict, _res.code

            _logger.info(f'Call API for validating dataset: {dataset_id}')

            try:
                dataset_node = get_dataset_by_id(dataset_id)
                if dataset_node['type'] != 'BIDS':
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result('Dataset is not BIDS type')
                    return _res.to_dict, _res.code

                if dataset_node['creator'] != current_identity['username']:
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_result('no permission for this dataset')
                    return _res.to_dict, _res.code
            except Exception as e:
                _res.code = EAPIResponseCode.bad_request
                _res.error_msg = f'error when get dataset node in dataset service: {e}'
                return _res.to_dict, _res.code

            try:
                url = ConfigClass.DATASET_SERVICE + 'dataset/verify/pre'
                data = {
                    'dataset_geid': dataset_id,
                    'type': 'bids'
                }
                response = requests.post(url, headers=request.headers, json=data)
                if response.status_code != 200:
                    _logger.error('Failed to verify dataset in dataset service:   ' + response.text)
                    _res.set_code(EAPIResponseCode.internal_error)
                    _res.set_result('Failed to verify dataset in dataset service:   ' + response.text)
                    return _res.to_dict, _res.code
                return response.json()

            except Exception as e:
                _res.code = EAPIResponseCode.bad_request
                _res.error_msg = f'error when verify dataset in service dataset: {e}'
                return _res.to_dict, _res.code

    class BIDSResult(Resource):
        @jwt_required()
        def get(self, dataset_id):
            _res = APIResponse()

            try:
                dataset_node = get_dataset_by_id(dataset_id)

                if dataset_node['creator'] != current_identity['username']:
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_result('no permission for this dataset')
                    return _res.to_dict, _res.code
            except Exception as e:
                _res.code = EAPIResponseCode.bad_request
                _res.error_msg = f'error when get dataset node in dataset service: {e}'
                return _res.to_dict, _res.code

            try:
                url = ConfigClass.DATASET_SERVICE + 'dataset/bids-msg/{}'.format(dataset_id)
                response = requests.get(url)
                if response.status_code != 200:
                    _logger.error('Failed to get dataset bids result in dataset service:   ' + response.text)
                    _res.set_code(EAPIResponseCode.internal_error)
                    _res.set_result('Failed to get dataset bids result in dataset service:   ' + response.text)
                    return _res.to_dict, _res.code
                else:
                    return response.json()

            except Exception as e:
                _res.code = EAPIResponseCode.bad_request
                _res.error_msg = f'error when get dataset bids result in service dataset: {e}'
                return _res.to_dict, _res.code
