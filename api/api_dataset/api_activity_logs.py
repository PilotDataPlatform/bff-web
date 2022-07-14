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

import httpx
from common import LoggerFactory
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi_utils import cbv
from starlette.datastructures import MultiDict

from app.auth import jwt_required
from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from resources.utils import get_dataset_by_code

_logger = LoggerFactory('api_dataset').get_logger()

router = APIRouter(tags=['Activity Logs'])


@cbv.cbv(router)
class ActivityLogs:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/activity-logs/{dataset_id}',
        summary='Fetch activity logs of a dataset from the search service',
    )
    async def get(self, dataset_id: str, request: Request):
        """Fetch activity logs of a dataset."""
        _res = APIResponse()
        _logger.info(f'Call API for fetching logs for dataset: {dataset_id}')

        url = ConfigClass.SEARCH_SERVICE + 'dataset-activity-logs/'
        try:
            dataset = await get_dataset_by_id(dataset_id=dataset_id)
            if not dataset:
                _res.set_code(EAPIResponseCode.bad_request)
                _res.set_result('Dataset does not exist')
                return _res.json_response()

            if dataset['creator'] != self.current_identity['username']:
                _res.set_code(EAPIResponseCode.forbidden)
                _res.set_result('No permission for this dataset')
                return _res.json_response()

            params = MultiDict(request.query_params)
            params['container_code'] = dataset['code']

            async with httpx.AsyncClient() as client:
                _logger.info(f'Calling search service {url} with query params: {params}')
                response = await client.get(url, params=params)

            if response.status_code != 200:
                _logger.error(f'Failed to query dataset activity log from search service: {response.text}')
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result(f'Failed to query dataset activity log from search service: {response.text}')
                return _res.json_response()
            else:
                return response.json()

        except Exception as e:
            _logger.error(f'Failed to query audit log from provenance service: {str(e)}')
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result(f'Failed to query audit log from provenance service: {str(e)}')
