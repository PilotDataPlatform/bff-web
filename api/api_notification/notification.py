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
from app.auth import jwt_required
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode


router = APIRouter(tags=["Notifications"])


@cbv.cbv(router)
class NotificationRestful:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/notification',
        summary="Get notifications",
    )
    async def get(self, request: Request):
        api_response = APIResponse()
        params = request.query_params
        response = requests.get(ConfigClass.NOTIFY_SERVICE + '/v1/notification', params=params)
        if response.status_code != 200:
            api_response.set_error_msg(response.json())
            return api_response.json_response()
        api_response.set_result(response.json())
        return api_response.json_response()

    @router.post(
        '/notification',
        summary="create notification",
    )
    async def post(self, request: Request):
        api_response = APIResponse()
        if self.current_identity["role"] != "admin":
            api_response.set_error_msg("Permission denied")
            api_response.set_code(EAPIResponseCode.forbidden)
            return api_response.json_response()
        body = await request.json()
        response = requests.post(ConfigClass.NOTIFY_SERVICE + '/v1/notification', json=body)
        if response.status_code != 200:
            api_response.set_error_msg(response.json())
            return api_response.json_response()
        api_response.set_result(response.json())
        return api_response.json_response()

    @router.put(
        '/notification',
        summary="update notification",
    )
    async def put(self, request: Request):
        api_response = APIResponse()
        if self.current_identity["role"] != "admin":
            api_response.set_error_msg("Permission denied")
            api_response.set_code(EAPIResponseCode.forbidden)
            return api_response.json_response()
        params = request.query_params
        body = await request.json()
        response = requests.put(ConfigClass.NOTIFY_SERVICE + '/v1/notification', params=params, json=body)
        if response.status_code != 200:
            api_response.set_error_msg(response.json())
            return api_response.json_response()
        api_response.set_result(response.json())
        return api_response.json_response()

    @router.delete(
        '/notification',
        summary="delete notification",
    )
    async def delete(self, request: Request):
        api_response = APIResponse()
        if self.current_identity["role"] != "admin":
            api_response.set_error_msg("Permission denied")
            api_response.set_code(EAPIResponseCode.forbidden)
            return api_response.json_response()
        params = request.query_params
        response = requests.delete(ConfigClass.NOTIFY_SERVICE + '/v1/notification', params=params)
        if response.status_code != 200:
            api_response.set_error_msg(response.json())
            return api_response.json_response()
        api_response.set_result(response.json())
        return api_response.json_response()


@cbv.cbv(router)
class NotificationsRestful:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/notifications',
        summary="list notification",
    )
    async def get(self, request: Request):
        api_response = APIResponse()
        params = request.query_params
        response = requests.get(ConfigClass.NOTIFY_SERVICE + '/v1/notifications', params=params)
        if response.status_code != 200:
            api_response.set_error_msg(response.json())
            return api_response.json_response()
        api_response.set_result(response.json())
        return api_response.json_response()
