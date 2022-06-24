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
from services.permissions_service.decorators import DatasetPermission

from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode


router = APIRouter(tags=["Dataset Schema"])

_logger = LoggerFactory('api_schema').get_logger()


@cbv.cbv(router)
class SchemaCreate:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/dataset/{dataset_id}/schema',
        summary="Create a new schema",
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        api_response = APIResponse()
        try:
            response = requests.post(ConfigClass.DATASET_SERVICE + 'schema', json=await request.json())
        except Exception as e:
            _logger.info(f'Error calling dataset service: {str(e)}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {str(e)}')
            return api_response.json_response()
        return response.json(), response.status_code


@cbv.cbv(router)
class Schema:
    current_identity: dict = Depends(jwt_required)

    @router.put(
        '/dataset/{dataset_id}/schema/{schema_id}',
        summary="Update a schema",
        dependencies=[Depends(DatasetPermission())],
    )
    async def put(self, dataset_id: str, schema_id: str, request: Request):
        api_response = APIResponse()
        payload = await request.json()
        payload['username'] = self.current_identity['username']
        try:
            response = requests.put(ConfigClass.DATASET_SERVICE + f'schema/{schema_id}', json=payload)
        except Exception as e:
            _logger.info(f'Error calling dataset service: {str(e)}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {str(e)}')
            return api_response.json_response()
        return response.json(), response.status_code

    @router.get(
        '/dataset/{dataset_id}/schema/{schema_id}',
        summary="Get a schema by id",
        dependencies=[Depends(DatasetPermission())],
    )
    async def get(self, dataset_id: str, schema_id: str):
        api_response = APIResponse()

        try:
            response = requests.get(ConfigClass.DATASET_SERVICE + f'schema/{schema_id}')
        except Exception as e:
            _logger.info(f'Error calling dataset service: {str(e)}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {str(e)}')
            return api_response.json_response()
        return response.json(), response.status_code

    @router.delete(
        '/dataset/{dataset_id}/schema/{schema_id}',
        summary="Delete a schema by id",
        dependencies=[Depends(DatasetPermission())],
    )
    async def delete(self, dataset_id: str, schema_id: str, request: Request):
        api_response = APIResponse()
        payload = await request.json()
        payload['username'] = self.current_identity['username']
        payload['dataset_geid'] = dataset_id
        try:
            response = requests.delete(ConfigClass.DATASET_SERVICE + f'schema/{schema_id}', json=payload)
        except Exception as e:
            _logger.info(f'Error calling dataset service: {str(e)}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {str(e)}')
            return api_response.json_response()
        return response.json(), response.status_code


@cbv.cbv(router)
class SchemaList:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/dataset/{dataset_id}/schema/list',
        summary="List schemas",
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        api_response = APIResponse()
        payload = await request.json()
        payload['creator'] = self.current_identity['username']
        payload['dataset_geid'] = dataset_id
        try:
            response = requests.post(ConfigClass.DATASET_SERVICE + 'schema/list', json=payload)
        except Exception as e:
            _logger.info(f'Error calling dataset service: {str(e)}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {str(e)}')
            return api_response.json_response()
        return response.json(), response.status_code
