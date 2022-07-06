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
import re
import pytest
import requests_mock
from uuid import uuid4
from config import ConfigClass

from app.main import create_app
from testcontainers.redis import RedisContainer
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock
from httpx import AsyncClient
from async_asgi_testclient import TestClient as TestAsyncClient


@pytest.fixture(scope='session')
def test_client(redis):
    ConfigClass.REDIS_URL = redis.url
    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_async_client(redis):
    ConfigClass.REDIS_URL = redis.url
    app = create_app()
    return TestAsyncClient(app)


@pytest.fixture
def requests_mocker():
    kw = {'real_http': True}
    with requests_mock.Mocker(**kw) as m:
        yield m


@pytest.fixture
def jwt_token_admin(mocker, httpx_mock):
    jwt_mock(mocker, httpx_mock, "admin")


@pytest.fixture
def jwt_token_contrib(mocker, httpx_mock):
    jwt_mock(mocker, httpx_mock, "member", "contributor", "test_project")


def jwt_mock(mocker, httpx_mock: HTTPXMock, platform_role: str, project_role: str = "", project_code: str = ""):
    if platform_role == "admin":
        roles = ["platform-admin"]
    else:
        roles = [f"{project_code}-{project_role}"]
    token = {
        "exp": 1651861167,
        "iat": 1651860867,
        "aud": "account",
        "sub": "admin",
        "typ": "Bearer",
        "acr": "1",
        "realm_access": {
            "roles": roles
        },
        "resource_access": {
            "account": {
                "roles": [
                ]
            }
        },
        "email_verified": True,
        "name": "test test",
        "preferred_username": "test",
        "given_name": "test",
        "family_name": "test",
        "email": "test@example.com",
        "group": roles,
    }
    mocker.patch("app.auth.get_token", return_value="")
    mocker.patch("jwt.decode", return_value=token)
    mock_data = {
        "result": {
            "id": str(uuid4()),
            "email": "test@example.com",
            "first_name": "test@example.com",
            "last_name": "test@example.com",
            "attributes": {
                "status": "active"
            },
            "role": platform_role,
            "realm_roles": []
        }
    }
    url = ConfigClass.AUTH_SERVICE + 'admin/user?username=test&exact=true'
    httpx_mock.add_response(
        method='GET',
        url=url,
        json=mock_data
    )


@pytest.fixture
def has_permission_true(mocker):
    mocker.patch("services.permissions_service.utils.has_permission", return_value=True)
    mocker.patch("services.permissions_service.decorators.has_permission", return_value=True)
    mocker.patch("api.api_files.meta.has_permission", return_value=True)
    mocker.patch("api.api_data_manifest.data_manifest.has_permission", return_value=True)
    mocker.patch("api.api_tags.utils.has_permission", return_value=True)


@pytest.fixture
def has_permission_false(mocker):
    mocker.patch("services.permissions_service.utils.has_permission", return_value=False)
    mocker.patch("services.permissions_service.decorators.has_permission", return_value=False)
    mocker.patch("api.api_files.meta.has_permission", return_value=False)
    mocker.patch("api.api_data_manifest.data_manifest.has_permission", return_value=False)
    mocker.patch("api.api_data_manifest.data_manifest.has_permissions", return_value=False)
    mocker.patch("api.api_tags.utils.has_permission", return_value=False)


@pytest.fixture
def has_project_contributor_role(mocker):
    mocker.patch("services.permissions_service.utils.get_project_role", return_value="contributor")
    mocker.patch("api.api_data_manifest.data_manifest.get_project_role", return_value="contributor")


@pytest.fixture
def has_invalid_project_role(mocker):
    mocker.patch("services.permissions_service.utils.get_project_role", return_value=None)
    mocker.patch("api.api_data_manifest.data_manifest.get_project_role", return_value=None)


#@pytest.fixture
#def request_context(app):
#    with app.test_request_context() as context:
#        yield context



@pytest.fixture(scope='session', autouse=True)
def redis():
    with RedisContainer("redis:latest") as redis:
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(redis.port_to_expose)
        redis.url = f"redis://{host}:{port}"
        yield redis
