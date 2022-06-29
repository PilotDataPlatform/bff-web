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

router = APIRouter(tags=["Knowledge Graph"])


# for backend services down/on testing
@cbv.cbv(router)
class KGResource:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/kg/resources',
        summary="Knowledge graph",
    )
    async def post(self, request: Request):
        url = ConfigClass.KG_SERVICE + "resources"
        payload_json = await request.json()
        respon = requests.post(url, json=payload_json, headers=request.headers)
        return respon.json(), respon.status_code
