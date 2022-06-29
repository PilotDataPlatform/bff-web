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
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from config import ConfigClass
from services.dataset import get_dataset_by_id
from services.permissions_service.decorators import (DatasetPermission,
                                                     DatasetPermissionByCode)

router = APIRouter(tags=["Dataset"])


@cbv.cbv(router)
class CodeRestful:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/dataset/dataset-peek/{dataset_code}',
        summary="Get dataset by code",
        dependencies=[Depends(DatasetPermissionByCode())]
    )
    def get(self, dataset_code: str):
        url = ConfigClass.DATASET_SERVICE + 'dataset-peek/{}'.format(dataset_code)
        respon = requests.get(url)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class Dataset:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/dataset/{dataset_id}',
        summary="Get dataset by id",
        dependencies=[Depends(DatasetPermission())]
    )
    async def get(self, dataset_id: str):
        url = ConfigClass.DATASET_SERVICE + 'dataset/{}'.format(dataset_id)
        respon = requests.get(url)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)

    @router.put(
        '/dataset/{dataset_id}',
        summary="Update dataset by id",
        dependencies=[Depends(DatasetPermission())]
    )
    async def put(self, dataset_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/{}'.format(dataset_id)
        payload_json = await request.json()
        respon = requests.put(url, json=payload_json, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class RestfulPost:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/dataset',
        summary="create dataset",
    )
    async def post(self, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset'
        payload_json = await request.json()
        operator_username = self.current_identity['username']
        payload_username = payload_json.get('username')
        if operator_username != payload_username:
            return JSONResponse(content={
                'err_msg': 'No permissions: {} cannot create dataset for {}'.format(
                    operator_username, payload_username)
            }, status_code=403)
        respon = requests.post(url, json=payload_json, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class List:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/users/{username}/datasets',
        summary="List users datasets",
    )
    async def post(self, username: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'users/{}/datasets'.format(username)

        # also check permission
        operator_username = self.current_identity['username']
        if operator_username != username:
            return JSONResponse(content={
                'err_msg': 'No permissions'
            }, status_code=403)

        payload_json = await request.json()
        respon = requests.post(url, json=payload_json, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class DatasetFiles:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/dataset/{dataset_id}/files',
        summary="List dataset files",
        dependencies=[Depends(DatasetPermission())],
    )
    def get(self, dataset_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/{}/files'.format(dataset_id)
        response = requests.get(url, params=request.query_params, headers=request.headers)
        if response.status_code != 200:
            return response.json(), response.status_code
        entities = []
        for file_node in response.json()["result"]["data"]:
            file_node["zone"] = "greenroom" if file_node["zone"] == 0 else "core"
            entities.append(file_node)
        result = response.json()
        result["result"]["data"] = entities
        return JSONResponse(content=result, status_code=response.status_code)

    @router.post(
        '/dataset/{dataset_id}/files',
        summary="Move dataset files",
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/{}/files'.format(dataset_id)
        payload_json = await request.json()
        respon = requests.post(url, json=payload_json, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)

    @router.put(
        '/dataset/{dataset_id}/files',
        summary="Recieve the file list from a project and Copy them under the dataset",
        dependencies=[Depends(DatasetPermission())],
    )
    async def put(self, dataset_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/{}/files'.format(dataset_id)
        payload_json = await request.json()
        respon = requests.put(url, json=payload_json, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)

    @router.delete(
        '/dataset/{dataset_id}/files',
        summary="Remove dataset files",
        dependencies=[Depends(DatasetPermission())],
    )
    async def delete(self, dataset_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/{}/files'.format(dataset_id)
        payload_json = await request.json()
        respon = requests.delete(url, json=payload_json, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class DatasetFileUpdate:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/dataset/{dataset_id}/files/{file_id}',
        summary="update files within the dataset",
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, file_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/{}/files/{}'.format(dataset_id, file_id)
        payload_json = await request.json()
        respon = requests.post(url, json=payload_json, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class DatsetTasks:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/dataset/{dataset_id}/file/tasks',
        summary="Dataset Tasks",
        dependencies=[Depends(DatasetPermission())],
    )
    async def get(self, dataset_id: str, request: Request):
        request_params = request.query_params
        new_params = {
            **request_params,
            'label': 'Dataset'
        }

        dataset = get_dataset_by_id(dataset_id)
        new_params['code'] = dataset['code']

        url = ConfigClass.DATA_UTILITY_SERVICE + 'tasks'
        response = requests.get(url, params=new_params)
        return JSONResponse(content=response.json(), status_code=response.status_code)

    @router.delete(
        '/dataset/{dataset_id}/file/tasks',
        summary="Dataset Tasks",
        dependencies=[Depends(DatasetPermission())],
    )
    async def delete(self, dataset_id: str, request: Request):
        request_body = await request.json()
        request_body.update({'label': 'Dataset'})

        dataset = get_dataset_by_id(dataset_id)
        request_body['code'] = dataset['code']

        url = ConfigClass.DATA_UTILITY_SERVICE + 'tasks'
        response = requests.delete(url, json=request_body)
        return JSONResponse(content=response.json(), status_code=response.status_code)
