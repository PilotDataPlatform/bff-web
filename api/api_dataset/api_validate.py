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
from fastapi import APIRouter, Depends, Request
from fastapi_utils import cbv
from services.permissions_service.decorators import DatasetPermission
from app.auth import jwt_required

from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.dataset import get_dataset_by_id

_logger = LoggerFactory('api_dataset_validator').get_logger()

router = APIRouter(tags=["Dataset Validate"])


@cbv.cbv(router)
class BIDSValidator:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/dataset/bids-validate',
        summary="verify a bids dataset.",
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, request: Request):
        _res = APIResponse()
        payload = await request.json()
        dataset_id = payload.get('dataset_geid', None)
        if not dataset_id:
            _res.set_code(EAPIResponseCode.bad_request)
            _res.set_error_msg('dataset_id is missing in payload')
            return _res.json_response()

        _logger.info(f'Call API for validating dataset: {dataset_id}')

        try:
            dataset_node = get_dataset_by_id(dataset_id)
            if dataset_node['type'] != 'BIDS':
                _res.set_code(EAPIResponseCode.bad_request)
                _res.set_result('Dataset is not BIDS type')
                return _res.json_response()
        except Exception as e:
            _res.code = EAPIResponseCode.bad_request
            _res.error_msg = f'error when get dataset node in dataset service: {e}'
            return _res.json_response()

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
                return _res.json_response()
            return response.json()

        except Exception as e:
            _res.code = EAPIResponseCode.bad_request
            _res.error_msg = f'error when verify dataset in service dataset: {e}'
            return _res.json_response()


@cbv.cbv(router)
class BIDSResult:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/dataset/bids-validate/{dataset_id}',
        summary="verify a bids dataset",
        dependencies=[Depends(DatasetPermission())],
    )
    def get(self, dataset_id: str):
        _res = APIResponse()
        try:
            url = ConfigClass.DATASET_SERVICE + 'dataset/bids-msg/{}'.format(dataset_id)
            response = requests.get(url)
            if response.status_code != 200:
                _logger.error('Failed to get dataset bids result in dataset service:   ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result('Failed to get dataset bids result in dataset service:   ' + response.text)
                return _res.json_response()
            return response.json()

        except Exception as e:
            _res.code = EAPIResponseCode.bad_request
            _res.error_msg = f'error when get dataset bids result in service dataset: {e}'
            return _res.json_response()
