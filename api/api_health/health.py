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
from fastapi import APIRouter
from fastapi.responses import Response
from fastapi_utils import cbv

router = APIRouter(tags=["Health"])


@cbv.cbv(router)
class Health:
    @router.get(
        '/health',
        summary="Health check",
    )
    async def get(self):
        return Response(status_code=204)
