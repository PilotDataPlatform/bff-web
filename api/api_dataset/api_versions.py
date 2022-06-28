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
from fastapi.responses import JSONResponse
from fastapi_utils import cbv
from app.auth import jwt_required

from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode

from services.permissions_service.decorators import DatasetPermission

#api_resource = module_api.namespace('DatasetProxy', description='Versions API', path='/v1/dataset/')
router = APIRouter(tags=["Dataset Version"])

_logger = LoggerFactory('api_versions').get_logger()


@cbv.cbv(router)
class Publish:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/dataset/{dataset_id}/publish',
        summary="Publish a new dataset version",
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        api_response = APIResponse()
        try:
            response = requests.post(
                ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/publish', json=await request.json()
            )
        except Exception as e:
            _logger.info(f'Error calling dataset service: {str(e)}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {str(e)}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), code=response.status_code)


@cbv.cbv(router)
class PublishStatus:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/dataset/{dataset_id}/publish/status',
        summary="Get status of publish",
        dependencies=[Depends(DatasetPermission())],
    )
    async def get(self, dataset_id: str, request: Request):
        api_response = APIResponse()
        try:
            response = requests.get(
                ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/publish/status', params=request.query_params
            )
        except Exception as e:
            _logger.info(f'Error calling dataset service: {str(e)}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {str(e)}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), code=response.status_code)


@cbv.cbv(router)
class DownloadPre:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/dataset/{dataset_id}/download/pre',
        summary="pre-download for dataset",
        dependencies=[Depends(DatasetPermission())],
    )
    async def get(self, dataset_id: str, request: Request):
        api_response = APIResponse()
        try:
            response = requests.get(
                ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/download/pre',
                params=request.query_params,
                headers=request.headers
            )
        except Exception as e:
            _logger.info(f'Error calling dataset service: {str(e)}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {str(e)}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), code=response.status_code)


@cbv.cbv(router)
class DatasetVersions:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/dataset/{dataset_id}/versions',
        summary="Get dataset versions",
        dependencies=[Depends(DatasetPermission())],
    )
    async def get(self, dataset_id: str, request: Request):
        api_response = APIResponse()
        try:
            response = requests.get(
                ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}/versions',
                params=request.query_params
            )
        except Exception as e:
            _logger.info(f'Error calling dataset service: {str(e)}')
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result(f'Error calling dataset service: {str(e)}')
            return api_response.json_response()
        return JSONResponse(content=response.json(), code=response.status_code)
