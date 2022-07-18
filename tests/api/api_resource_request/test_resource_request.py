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
from uuid import uuid4
import pytest


RESOURCE_REQUEST = {
    "project_id": str(uuid4()),
    "user_id": str(uuid4()),
    "username": "test@test.com",
    "email": "test@test.com",
    "requested_for": "SuperSet",
    "completed_at": "2022-07-05T14:27:14.834812+00:00",
    "id": str(uuid4())
}

PROJECT = {
    "id": RESOURCE_REQUEST["project_id"],
    "name": "testproject",
    "code": "test_project",
}

USER = {
    "id": RESOURCE_REQUEST["user_id"],
    "email": "test@test.com",
    "name": "test",
    "username": "test",
}


def test_get_request_200(test_client, httpx_mock, jwt_token_admin, has_permission_true):
    request_id = RESOURCE_REQUEST["id"]
    httpx_mock.add_response(
        method="GET",
        url=ConfigClass.PROJECT_SERVICE + f"/v1/resource-requests/{request_id}",
        json=RESOURCE_REQUEST,
        status_code=200
    )
    response = test_client.get(f"/v1/resource-request/{request_id}")
    assert response.status_code == 200


def test_get_request_403(test_client, httpx_mock, jwt_token_contrib, has_permission_false):
    request_id = RESOURCE_REQUEST["id"]
    response = test_client.get(f"/v1/resource-request/{request_id}")
    assert response.status_code == 403


def test_delete_request_200(test_client, httpx_mock, jwt_token_admin, has_permission_true):
    request_id = RESOURCE_REQUEST["id"]
    httpx_mock.add_response(
        method="DELETE",
        url=ConfigClass.PROJECT_SERVICE + f"/v1/resource-requests/{request_id}",
        json=RESOURCE_REQUEST,
        status_code=204
    )
    response = test_client.delete(f"/v1/resource-request/{request_id}/")
    assert response.status_code == 200


def test_delete_request_400(test_client, httpx_mock, jwt_token_admin, has_permission_true):
    request_id = RESOURCE_REQUEST["id"]
    httpx_mock.add_response(
        method="DELETE",
        url=ConfigClass.PROJECT_SERVICE + f"/v1/resource-requests/{request_id}",
        json=RESOURCE_REQUEST,
        status_code=400
    )
    response = test_client.delete(f"/v1/resource-request/{request_id}/")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_put_request_complete_200(
    test_async_client,
    requests_mocker,
    httpx_mock,
    jwt_token_admin,
    has_permission_true
):
    request_id = RESOURCE_REQUEST["id"]
    project_id = RESOURCE_REQUEST["project_id"]
    user_id = RESOURCE_REQUEST["user_id"]

    httpx_mock.add_response(
        method="GET",
        url=ConfigClass.PROJECT_SERVICE + f"/v1/projects/{project_id}",
        json=PROJECT,
        status_code=200
    )

    httpx_mock.add_response(
        method="PATCH",
        url=ConfigClass.PROJECT_SERVICE + f"/v1/resource-requests/{request_id}",
        json=RESOURCE_REQUEST,
        status_code=200
    )

    httpx_mock.add_response(
        method="GET",
        url=ConfigClass.AUTH_SERVICE + f"admin/user?user_id={user_id}&exact=true",
        json={'result': USER},
        status_code=200
    )

    httpx_mock.add_response(
        method="POST",
        url=ConfigClass.NOTIFY_SERVICE + "email/",
        json={'result': 'success'},
        status_code=200
    )

    response = await test_async_client.put(f"/v1/resource-request/{request_id}/complete")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_put_request_complete_500(
    test_async_client,
    requests_mocker,
    httpx_mock,
    jwt_token_admin,
    has_permission_true
):
    request_id = RESOURCE_REQUEST["id"]
    user_id = RESOURCE_REQUEST["user_id"]

    httpx_mock.add_response(
        method="PATCH",
        url=ConfigClass.PROJECT_SERVICE + f"/v1/resource-requests/{request_id}",
        json=RESOURCE_REQUEST,
        status_code=200
    )

    httpx_mock.add_response(
        method="GET",
        url=ConfigClass.AUTH_SERVICE + f"admin/user?user_id={user_id}&exact=true",
        json={'result': USER},
        status_code=500
    )

    response = await test_async_client.put(f"/v1/resource-request/{request_id}/complete")
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_post_request_query_200(
    test_async_client,
    httpx_mock,
    jwt_token_admin,
    has_permission_true
):

    result = {
        "num_of_pages": 1,
        "page": 0,
        "total": 1,
        "result": [
            RESOURCE_REQUEST
        ]
    }
    url = ConfigClass.PROJECT_SERVICE + (
        "/v1/resource-requests/?page=0&page_size=25&sort_by=requested_at&sort_order=asc"
    )
    httpx_mock.add_response(
        method="GET",
        url=url,
        json=result,
        status_code=200
    )

    payload = {
        "page": 0,
        "page_size": 25,
    }
    response = await test_async_client.post("/v1/resource-requests/query", json=payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_request_query_contrib_200(
    test_async_client,
    httpx_mock,
    jwt_token_contrib,
    has_permission_true
):

    result = {
        "num_of_pages": 1,
        "page": 0,
        "total": 1,
        "result": [
            RESOURCE_REQUEST
        ]
    }
    url = ConfigClass.PROJECT_SERVICE + (
        "/v1/resource-requests/""?page=0&page_size=25&sort_by=requested_at&sort_order=asc"
    )
    httpx_mock.add_response(
        method="GET",
        url=url,
        json=result,
        status_code=200
    )

    payload = {
        "page": 0,
        "page_size": 25,
    }
    response = await test_async_client.post("/v1/resource-requests/query", json=payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_request_create_200(
    test_async_client,
    httpx_mock,
    jwt_token_contrib,
    has_permission_true
):

    project_id = RESOURCE_REQUEST["project_id"]

    url = ConfigClass.PROJECT_SERVICE + "/v1/resource-requests/"
    httpx_mock.add_response(
        method="POST",
        url=url,
        json=RESOURCE_REQUEST,
        status_code=200
    )

    httpx_mock.add_response(
        method="GET",
        url=ConfigClass.AUTH_SERVICE + f"admin/user?username={ConfigClass.RESOURCE_REQUEST_ADMIN}",
        json={'result': USER},
        status_code=200
    )

    httpx_mock.add_response(
        method="POST",
        url=ConfigClass.NOTIFY_SERVICE + "email/",
        json={'result': 'success'},
        status_code=200
    )

    payload = {
        "user_id": RESOURCE_REQUEST["user_id"],
        "project_id": project_id,
        "request_for": "SuperSet",
    }
    response = await test_async_client.post("/v1/resource-requests", json=payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_request_create_403(
    test_async_client,
    httpx_mock,
    jwt_token_contrib,
    has_permission_true
):

    different_project = PROJECT.copy()
    different_project["id"] = str(uuid4())
    different_project["code"] = "different_project"
    project_id = different_project["id"]
    httpx_mock.add_response(
        method="GET",
        url=ConfigClass.PROJECT_SERVICE + f"/v1/projects/{project_id}",
        json=different_project,
        status_code=200
    )

    payload = {
        "user_id": RESOURCE_REQUEST["user_id"],
        "project_id": project_id,
        "request_for": "SuperSet",
    }
    response = await test_async_client.post("/v1/resource-requests", json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_post_request_create_500(
    test_async_client,
    httpx_mock,
    jwt_token_contrib,
    has_permission_true
):
    project_id = RESOURCE_REQUEST["project_id"]

    url = ConfigClass.PROJECT_SERVICE + "/v1/resource-requests/"
    httpx_mock.add_response(
        method="POST",
        url=url,
        json=RESOURCE_REQUEST,
        status_code=500
    )

    payload = {
        "user_id": RESOURCE_REQUEST["user_id"],
        "project_id": project_id,
        "request_for": "SuperSet",
    }
    response = await test_async_client.post("/v1/resource-requests", json=payload)
    assert response.status_code == 500
