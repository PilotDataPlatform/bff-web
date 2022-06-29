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
import json

import requests
from common import LoggerFactory
from fastapi import APIRouter, Depends, Request
from fastapi_utils import cbv

from app.auth import jwt_required
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from resources.utils import get_dataset

_logger = LoggerFactory('api_dataset').get_logger()

router = APIRouter(tags=["Activity Logs"])


@cbv.cbv(router)
class ActivityLogs:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/activity-logs/{dataset_id}',
        summary="Fetch activity logs of a dataset",
    )
    def get(self, dataset_id: str, request: Request):
        """Fetch activity logs of a dataset."""
        _res = APIResponse()
        _logger.info(
            f'Call API for fetching logs for dataset: {dataset_id}')

        url = ConfigClass.DATASET_SERVICE + 'activity-logs'

        try:
            dataset = get_dataset(dataset_id=dataset_id)
            if not dataset:
                _res.set_code(EAPIResponseCode.bad_request)
                _res.set_result('Dataset does not exist')
                return _res.json_response()

            if dataset['creator'] != self.current_identity['username']:
                _res.set_code(EAPIResponseCode.forbidden)
                _res.set_result('No permission for this dataset')
                return _res.json_response()

            query = request.query_params.get('query', '{}')
            page_size = int(request.query_params.get('page_size', 10))
            page = int(request.query_params.get('page', 0))
            order_by = request.query_params.get('order_by', 'create_timestamp')
            order_type = request.query_params.get('order_type', 'desc')

            query_info = json.loads(query)
            query_info['dataset_geid'] = {
                'value': dataset_id,
                'condition': 'equal'
            }

            params = {
                'query': json.dumps(query_info),
                'page_size': page_size,
                'page': page,
                'sort_by': order_by,
                'sort_type': order_type,
            }
            response = requests.get(url, params=params)

            if response.status_code != 200:
                _logger.error(
                    'Failed to query activity log from dataset service:   ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result(
                    'Failed to query activity log from dataset service:   ' + response.text)
                return _res.json_response()
            else:
                return response.json()

        except Exception as e:
            _logger.error(
                'Failed to query audit log from provenance service:   ' + str(e))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result(
                'Failed to query audit log from provenance service:   ' + str(e))


@cbv.cbv(router)
class ActivityLogByVersion:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/activity-logs/version/{dataset_id}',
        summary="Fetch activity logs of a dataset by version",
    )
    def get(self, dataset_id: str, request: Request):
        """Fetch activity logs of a dataset by version number."""
        _res = APIResponse()
        _logger.info(f'Call API for fetching logs for dataset: {dataset_id}')

        url = ConfigClass.DATASET_SERVICE + 'activity-logs/{}'.format(dataset_id)

        try:
            dataset = get_dataset(dataset_id=dataset_id)
            if not dataset:
                _res.set_code(EAPIResponseCode.bad_request)
                _res.set_result('Dataset does not exist')
                return _res.json_response()

            page_size = int(request.query_params.get('page_size', 10))
            page = int(request.query_params.get('page', 0))
            order_by = request.query_params.get('order_by', 'create_timestamp')
            order_type = request.query_params.get('order_type', 'desc')
            version = request.query_params.get('version', '1')

            params = {
                'page_size': page_size,
                'page': page,
                'sort_by': order_by,
                'sort_type': order_type,
                'version': version
            }
            response = requests.get(url, params=params)

            if response.status_code != 200:
                _logger.error(
                    'Failed to query activity log from dataset service:   ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result(
                    'Failed to query activity log from dataset service:   ' + response.text)
                return _res.json_response()
            else:
                return response.json()

        except Exception as e:
            _logger.error(
                'Failed to query audit log from provenance service:   ' + str(e))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result(
                'Failed to query audit log from provenance service:   ' + str(e))
