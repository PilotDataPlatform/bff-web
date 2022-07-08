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
from config import ConfigClass
from services.permissions_service.utils import has_permission
from resources.error_handler import APIException
from uuid import uuid4
import pytest


MOCK_ADMINS = [
    {
        "username": "admin",
        "name": "admin",
        "email": "admin@test.com",
    }
]

PROJECT_DATA = {
    "code": "unittestproject",
    "name": "Unit test project",
    "description": "test",
    "tags": ["test1", "test2"],
    "is_discoverable": True,
    "icon": "fake"
}


@pytest.mark.asyncio
async def test_create_project_200(
    test_async_client,
    mocker, requests_mocker,
    httpx_mock,
    jwt_token_admin,
    has_permission_true
):
    payload = PROJECT_DATA.copy()
    json_response = PROJECT_DATA.copy()
    json_response["id"] = str(uuid4())
    mocker.patch('api.api_project_v2.create_minio_bucket', return_value=None)
    mocker.patch('api.api_project_v2.ldap_create_user_group', return_value=None)

    # create name folders
    requests_mocker.post(
        ConfigClass.METADATA_SERVICE + "items/batch/",
        json={},
        status_code=200
    )

    # create keycloak group
    requests_mocker.post(
        ConfigClass.AUTH_SERVICE + "admin/users/realm-roles",
        json={},
        status_code=200
    )

    # get all platform admins
    requests_mocker.post(
        ConfigClass.AUTH_SERVICE + "admin/roles/users",
        json={"result": [{"name": "test"}]},
        status_code=200
    )

    # duplicate check
    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.PROJECT_SERVICE + "/v1/projects/" + payload.get("code"),
        json={},
        status_code=404
    )

    # icon
    project_id = json_response["id"]
    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.PROJECT_SERVICE + f"/v1/projects/{project_id}/logo",
        json=payload
    )

    # create project
    httpx_mock.add_response(
        method='POST',
        url=ConfigClass.PROJECT_SERVICE + "/v1/projects/",
        json=json_response
    )

    headers = {"Authorization": ""}
    response = await test_async_client.post("/v1/projects", json=payload, headers=headers)
    assert response.status_code == 200


def test_create_project_409(
    test_client,
    mocker, requests_mocker,
    httpx_mock,
    jwt_token_admin,
    has_permission_true
):
    payload = PROJECT_DATA.copy()
    mocker.patch('api.api_project_v2.create_minio_bucket', return_value=None)
    mocker.patch('api.api_project_v2.ldap_create_user_group', return_value=None)

    # create name folders
    requests_mocker.post(
        ConfigClass.METADATA_SERVICE + "items/batch/",
        json={},
        status_code=200
    )

    # create keycloak group
    requests_mocker.post(
        ConfigClass.AUTH_SERVICE + "admin/users/realm-roles",
        json={},
        status_code=200
    )

    # get all platform admins
    requests_mocker.post(
        ConfigClass.AUTH_SERVICE + "admin/roles/users",
        json={},
        status_code=200
    )

    # duplicate check
    httpx_mock.add_response(
        method='GET',
        url=ConfigClass.PROJECT_SERVICE + "/v1/projects/" + payload.get("code"),
        json={},
        status_code=200
    )

    headers = {"Authorization": ""}
    response = test_client.post("/v1/projects", json=payload, headers=headers)
    assert response.status_code == 409


def test_create_project_missing_code_400(
    test_client,
    mocker, requests_mocker,
    httpx_mock,
    jwt_token_admin,
    has_permission_true
):
    payload = PROJECT_DATA.copy()
    del payload["code"]
    mocker.patch('api.api_project_v2.create_minio_bucket', return_value=None)
    mocker.patch('api.api_project_v2.ldap_create_user_group', return_value=None)

    # create name folders
    requests_mocker.post(
        ConfigClass.METADATA_SERVICE + "items/batch/",
        json={},
        status_code=200
    )

    # create keycloak group
    requests_mocker.post(
        ConfigClass.AUTH_SERVICE + "admin/users/realm-roles",
        json={},
        status_code=200
    )

    # get all platform admins
    requests_mocker.post(
        ConfigClass.AUTH_SERVICE + "admin/roles/users",
        json={},
        status_code=200
    )

    headers = {"Authorization": ""}
    response = test_client.post("/v1/projects", json=payload, headers=headers)
    assert response.status_code == 400


def test_create_project_bad_code_400(
    test_client,
    mocker, requests_mocker,
    httpx_mock,
    jwt_token_admin,
    has_permission_true
):
    payload = PROJECT_DATA.copy()
    payload["code"] = "bad!"
    mocker.patch('api.api_project_v2.create_minio_bucket', return_value=None)
    mocker.patch('api.api_project_v2.ldap_create_user_group', return_value=None)

    # create name folders
    requests_mocker.post(
        ConfigClass.METADATA_SERVICE + "items/batch/",
        json={},
        status_code=200
    )

    # create keycloak group
    requests_mocker.post(
        ConfigClass.AUTH_SERVICE + "admin/users/realm-roles",
        json={},
        status_code=200
    )

    # get all platform admins
    requests_mocker.post(
        ConfigClass.AUTH_SERVICE + "admin/roles/users",
        json={},
        status_code=200
    )

    headers = {"Authorization": ""}
    response = test_client.post("/v1/projects", json=payload, headers=headers)
    assert response.status_code == 400


def test_create_project_bad_name_400(
    test_client,
    mocker, requests_mocker,
    httpx_mock,
    jwt_token_admin,
    has_permission_true
):
    payload = PROJECT_DATA.copy()
    mocker.patch('api.api_project_v2.create_minio_bucket', return_value=None)
    mocker.patch('api.api_project_v2.ldap_create_user_group', return_value=None)
    payload["name"] = "".join(str(i) for i in range(1000))

    # create name folders
    requests_mocker.post(
        ConfigClass.METADATA_SERVICE + "items/batch/",
        json={},
        status_code=200
    )

    # create keycloak group
    requests_mocker.post(
        ConfigClass.AUTH_SERVICE + "admin/users/realm-roles",
        json={},
        status_code=200
    )

    # get all platform admins
    requests_mocker.post(
        ConfigClass.AUTH_SERVICE + "admin/roles/users",
        json={},
        status_code=200
    )

    headers = {"Authorization": ""}
    response = test_client.post("/v1/projects", json=payload, headers=headers)
    assert response.status_code == 400
