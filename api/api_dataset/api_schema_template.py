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
from fastapi_utils import cbv
from fastapi.responses import JSONResponse
from app.auth import jwt_required
from config import ConfigClass
from services.permissions_service.decorators import DatasetPermission

router = APIRouter(tags=["Dataset Schema Template"])


@cbv.cbv(router)
class SchemaTemplate:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/dataset/{dataset_id}/schemaTPL/{template_id}',
        summary="Get schema template by id",
        dependencies=[Depends(DatasetPermission())],
    )
    async def get(self, dataset_id: str, template_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/{}/schemaTPL/{}'.format(dataset_id, template_id)
        respon = requests.get(url, params=request.query_params, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)

    @router.put(
        '/dataset/{dataset_id}/schemaTPL/{template_id}',
        summary="Update schema template by id",
        dependencies=[Depends(DatasetPermission())],
    )
    async def put(self, dataset_id: str, template_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/{}/schemaTPL/{}'.format(dataset_id, template_id)
        payload_json = await request.json()
        respon = requests.put(url, json=payload_json, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)

    @router.delete(
        '/dataset/{dataset_id}/schemaTPL/{template_id}',
        summary="Delete schema template by id",
        dependencies=[Depends(DatasetPermission())],
    )
    async def delete(self, dataset_id: str, template_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/{}/schemaTPL/{}'.format(dataset_id, template_id)
        payload_json = await request.json()
        respon = requests.delete(url, json=payload_json, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class SchemaTemplateCreate:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/dataset/{dataset_id}/schemaTPL',
        summary="Create schema template",
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/{}/schemaTPL'.format(dataset_id)
        payload_json = await request.json()
        respon = requests.post(url, json=payload_json, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class SchemaTemplatePostQuery:
    @router.post(
        '/dataset/{dataset_id}/schemaTPL/list',
        summary="List and query schema templates",
        dependencies=[Depends(DatasetPermission())],
    )
    async def post(self, dataset_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/{}/schemaTPL/list'.format(dataset_id)
        payload_json = await request.json()
        respon = requests.post(url, json=payload_json, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)

###################################################################################################


# note this api will have different policy
@cbv.cbv(router)
class SchemaTemplateDefaultQuery:
    @router.post(
        '/dataset/schemaTPL/list',
        summary="List and query schema templates",
    )
    async def post(self, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/default/schemaTPL/list'
        payload_json = await request.json()
        respon = requests.post(url, json=payload_json, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)


@cbv.cbv(router)
class SchemaTemplateDefaultGet:
    @router.get(
        '/dataset/schemaTPL/list',
        summary="Get default schema",
    )
    async def get(self, template_id: str, request: Request):
        url = ConfigClass.DATASET_SERVICE + 'dataset/default/schemaTPL/{}'.format(template_id)
        respon = requests.get(url, params=request.args, headers=request.headers)
        return JSONResponse(content=respon.json(), status_code=respon.status_code)
