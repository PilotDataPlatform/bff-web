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
from app.auth import jwt_required

from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.permissions_service.decorators import DatasetPermission

router = APIRouter(tags=["Dataset Folder"])

_logger = LoggerFactory('api_versions').get_logger()


@cbv.cbv(router)
class DatasetFolder:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/dataset/{dataset_id}/folder',
        summary="Create empty folder in dataset",
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        _logger.info('POST dataset folder proxy')
        api_response = APIResponse()
        data = await request.json()
        payload = {
            'username': self.current_identity['username'],
            **data
        }
        try:
            response = requests.post(ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/folder', json=payload)
        except Exception as e:
            _logger.info(f'Error calling dataset service: {str(e)}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {str(e)}')
            return api_response.to_dict, api_response.code
        return response.json(), response.status_code
