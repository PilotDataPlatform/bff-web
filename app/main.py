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
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from resources.error_handler import APIException

from config import ConfigClass
from common import ProjectException
from app.api_registry import api_registry
from app.auth import jwt_required


def create_app():
    """create app function."""
    app = FastAPI(
        title='BFF Web',
        description='Back-end for Frontend Web',
        docs_url='/v1/api-doc',
        version=ConfigClass.version
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins='*',
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )


    @app.exception_handler(APIException)
    async def http_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.content,
        )

    @app.exception_handler(ProjectException)
    def project_exception_handler(exc: ProjectException):
        return exc.content, exc.status_code

    api_registry(app)

    return app
