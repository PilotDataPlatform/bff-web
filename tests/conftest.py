import os

import pytest
import requests_mock
from uuid import uuid4
from config import ConfigClass

from app import Flask
from app import create_app
from testcontainers.redis import RedisContainer


@pytest.fixture
def app():
    app = Flask('flask_test', root_path=os.path.dirname(__file__))
    return app


@pytest.fixture(scope='session')
def test_client(redis):
    ConfigClass.REDIS_URL = redis.url
    app = create_app()
    return app.test_client()


@pytest.fixture
def requests_mocker():
    kw = {'real_http': True}
    with requests_mock.Mocker(**kw) as m:
        yield m


@pytest.fixture
def jwt_token_admin(mocker, requests_mocker):
    jwt_mock(mocker, requests_mocker, "admin")


@pytest.fixture
def jwt_token_contrib(mocker, requests_mocker):
    jwt_mock(mocker, requests_mocker, "member", "contributor", "test_project")


def jwt_mock(mocker, requests_mocker, platform_role: str, project_role: str = "", project_code: str = ""):
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
        }
    }
    requests_mocker.get(ConfigClass.AUTH_SERVICE + "admin/user", json=mock_data)


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



@pytest.fixture
def request_context(app):
    with app.test_request_context() as context:
        yield context


@pytest.fixture(scope='session', autouse=True)
def redis():
    with RedisContainer("redis:latest") as redis:
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(redis.port_to_expose)
        redis.url = f"redis://{host}:{port}"
        yield redis
