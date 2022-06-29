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
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from services.permissions_service.decorators import PermissionsCheck

from .utils import get_collection_by_id

_logger = LoggerFactory('api_files_ops_v1').get_logger()

router = APIRouter(tags=["Collections"])


@cbv.cbv(router)
class VirtualFolderFiles:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/collections/{collection_id}/files',
        summary="Get items from vfolder",
    )
    async def post(self, collection_id: str, request: Request):
        """
        Add items to vfolder
        """
        _res = APIResponse()

        try:
            # Get collection
            vfolder = get_collection_by_id(collection_id)
            if self.current_identity["role"] != "admin":
                if vfolder["owner"] != self.current_identity["username"]:
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result("no permission for this project")
                    return _res.json_response()

            data = await request.json()
            data['id'] = collection_id
            url = f'{ConfigClass.METADATA_SERVICE}collection/items/'
            response = requests.post(url, json=data)
            if response.status_code != 200:
                _logger.error('Failed to add items to collection:   ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result("Failed to add items to collection")
                return _res.json_response()
            else:
                _logger.info('Successfully add items to collection: {}'.format(json.dumps(response.json())))
                return response.json()

        except Exception as e:
            _logger.error("errors in add items to collection: {}".format(str(e)))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to add items to collection")
            return _res.json_response()

    @router.delete(
        '/collections/{collection_id}/files',
        summary="Remove items from vfolder",
    )
    def delete(self, collection_id: str, request: Request):
        """
        Delete items from vfolder
        """

        _res = APIResponse()

        try:
            # Get collection
            vfolder = get_collection_by_id(collection_id)
            if self.current_identity["role"] != "admin":
                if vfolder["owner"] != self.current_identity["username"]:
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result("no permission for this project")
                    return _res.json_response()

            data = request.get_json()
            data['id'] = collection_id
            url = f'{ConfigClass.METADATA_SERVICE}collection/items/'
            response = requests.delete(url, json=data)
            if response.status_code != 200:
                _logger.error('Failed to remove items from collection:   ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result("Failed to remove items from collection")
                return _res.json_response()

            else:
                _logger.info('Successfully remove items from collection: {}'.format(json.dumps(response.json())))
                return response.json()

        except Exception as e:
            _logger.error("errors in remove items from collection: {}".format(str(e)))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to remove items from collection")
            return _res.json_response()

    @router.get(
        '/collections/{collection_id}/files',
        summary="get items from vfolder",
    )
    async def get(self, collection_id: str, request: Request):

        """
        Get items from vfolder
        """
        _res = APIResponse()

        try:
            # Get collection
            vfolder = get_collection_by_id(collection_id)
            if self.current_identity["role"] != "admin":
                if vfolder["owner"] != self.current_identity["username"]:
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result("no permission for this project")
                    return _res.json_response()

            url = f'{ConfigClass.METADATA_SERVICE}collection/items/'
            params = {'id': collection_id}
            response = requests.get(url, params=params)
            if response.status_code != 200:
                _logger.error('Failed to get items from collection:   ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result("Failed to get items from collection")
                return _res.json_response()
            else:
                _logger.info('Successfully retrieved items from collection: {}'.format(json.dumps(response.json())))
                return response.json()

        except Exception as e:
            _logger.error("errors in retrieve items to collection: {}".format(str(e)))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to retrieve items from collection")
            return _res.json_response()


@cbv.cbv(router)
class VirtualFolder:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/collections',
        summary="Get collections",
        dependencies=[Depends(PermissionsCheck('collections', 'core', 'view'))]
    )
    async def get(self, request: Request):
        payload = {
            "owner": self.current_identity['username'],
            'container_code': request.query_params.get('project_code')
        }
        response = requests.get(f'{ConfigClass.METADATA_SERVICE}collection/search/', params=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.post(
        '/collections',
        summary="Create collection",
        dependencies=[Depends(PermissionsCheck('collections', 'core', 'create'))]
    )
    async def post(self, request: Request):
        data = await request.json()
        payload = {
            "owner": self.current_identity['username'],
            **data,
            'container_code': request.query_params.get('project_code'),
        }
        payload['container_code'] = payload.pop('project_code')
        response = requests.post(f'{ConfigClass.METADATA_SERVICE}collection/', json=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)


@cbv.cbv(router)
class VirtualFolderInfo:
    current_identity: dict = Depends(jwt_required)

    @router.delete(
        '/collections/{collection_id}',
        summary="delete collection",
    )
    def delete(self, collection_id: str, request: Request):
        _res = APIResponse()

        try:
            # Get collection
            vfolder = get_collection_by_id(collection_id)

            if self.current_identity["role"] != "admin":
                if vfolder["owner"] != self.current_identity["username"]:
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result("no permission for this project")
                    return _res.json_response()

            url = f'{ConfigClass.METADATA_SERVICE}collection/'
            params = {'id': collection_id}
            response = requests.delete(url, params=params)
            if response.status_code != 200:
                _logger.error('Failed to delete collection:   ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result("Failed to delete collection")
                return _res.json_response()
            else:
                _logger.info(f'Successfully delete collection: {collection_id}')
                return response.json()
        except Exception as e:
            _logger.error("errors in delete collection: {}".format(str(e)))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to delete collection")
            return _res.json_response()
