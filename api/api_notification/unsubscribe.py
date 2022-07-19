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
from models.api_response import APIResponse
from services.permissions_service.decorators import PermissionsCheck

router = APIRouter(tags=["Unsubscribe"])


@cbv.cbv(router)
class UnsubscribeRestful:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/unsubscribe',
        summary="Create entry",
    )
    async def post(self, request: Request):
        api_response = APIResponse()
        body = await request.json()
        response = requests.post(ConfigClass.NOTIFY_SERVICE + 'unsubscribe', json=body)
        if response.status_code != 200:
            api_response.set_error_msg(response.json())
            return api_response.json_response()
        api_response.set_result(response.json())
        return api_response.json_response()
