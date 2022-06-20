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

from .utils import check_dataset_permissions

api_resource = module_api.namespace('DatasetProxy', description='Folder  API', path='/v1/dataset/')

_logger = LoggerFactory('api_versions').get_logger()


class APIDatasetFolder(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(self.DatasetFolder, '/<dataset_id>/folder')

    class DatasetFolder(Resource):
        @jwt_required()
        def post(self, dataset_id):
            _logger.info('POST dataset folder proxy')
            api_response = APIResponse()
            valid, response = check_dataset_permissions(dataset_id)
            if not valid:
                return response.to_dict, response.code

            payload = {
                'username': current_identity['username'],
                **request.get_json()
            }
            try:
                response = requests.post(ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/folder', json=payload)
            except Exception as e:
                _logger.info(f'Error calling dataset service: {str(e)}')
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result(f'Error calling dataset service: {str(e)}')
                return api_response.to_dict, api_response.code
            return response.json(), response.status_code
