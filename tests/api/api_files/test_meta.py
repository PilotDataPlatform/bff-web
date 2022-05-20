import pytest
from uuid import uuid4
from config import ConfigClass

MOCK_FILE_DATA = {
    "archived": False,
    "container_code": "test_project",
    "container_type": "project",
    "created_time": "2021-05-10 19:43:55.382824",
    "extended": {
        "extra": {
            "attributes": {},
            "system_tags": [],
            "tags": []
        },
        "id": str(uuid4())
    },
    "id": str(uuid4()),
    "last_updated_time": "2021-05-10 19:43:55.383021",
    "name": "jiang_folder_2",
    "owner": "admin",
    "parent": str(uuid4()),
    "parent_path": "test",
    "restore_path": None,
    "size": 0,
    "storage": {
        "id": str(uuid4()),
        "location_uri": None,
        "version": None
    },
    "type": "folder",
    "zone": 1
}


def test_list_meta_admin_200(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    mock_data = {
        "result": [
            MOCK_FILE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/search", json=mock_data)

    mock_data = {
        "result": MOCK_FILE_DATA
    }
    file_id = MOCK_FILE_DATA["parent"]
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f"item/{file_id}", json=mock_data)

    payload = {
        "zone": "greenroom",
        "source_type": "folder",
        "parent_path": MOCK_FILE_DATA["parent_path"],
        "project_code": "test_project"
    }
    headers = {"Authorization": jwt_token_admin}
    response = test_client.get("v2/files/meta", query_string=payload, headers=headers)
    assert response.status_code == 200


def test_list_meta_contrib_200(test_client, requests_mocker, jwt_token_contrib, has_permission_true):
    mock_data = {
        "result": [
            MOCK_FILE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/search", json=mock_data)

    mock_data = {
        "result": MOCK_FILE_DATA
    }
    file_id = MOCK_FILE_DATA["parent"]
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f"item/{file_id}", json=mock_data)

    payload = {
        "zone": "core",
        "source_type": "folder",
        "parent_path": MOCK_FILE_DATA["parent_path"],
        "project_code": "test_project"
    }
    headers = {"Authorization": jwt_token_contrib}
    response = test_client.get("v2/files/meta", query_string=payload, headers=headers)
    assert response.status_code == 200


def test_list_meta_wrong_project_403(test_client, requests_mocker, jwt_token_contrib, has_permission_false):
    mock_data = {
        "result": [
            MOCK_FILE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/search", json=mock_data)

    mock_data = {
        "result": MOCK_FILE_DATA
    }
    file_id = MOCK_FILE_DATA["parent"]
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f"item/{file_id}", json=mock_data)

    payload = {
        "zone": "greenroom",
        "source_type": "folder",
        "parent_path": MOCK_FILE_DATA["parent_path"],
        "project_code": "wrong_project"
    }
    headers = {"Authorization": jwt_token_contrib}
    response = test_client.get("v2/files/meta", query_string=payload, headers=headers)
    assert response.status_code == 403


def test_list_meta_contrib_permissions_403(test_client, requests_mocker, jwt_token_contrib, has_permission_true):
    file_data = MOCK_FILE_DATA.copy()
    file_data["parent_path"] = "admin"
    mock_data = {
        "result": [
           file_data
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/search", json=mock_data)

    mock_data = {
        "result": file_data
    }
    file_id = MOCK_FILE_DATA["parent"]
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f"item/{file_id}", json=mock_data)

    payload = {
        "zone": "greenroom",
        "source_type": "folder",
        "parent_path": "admin",
        "project_code": "test_project"
    }
    headers = {"Authorization": jwt_token_contrib}
    response = test_client.get("v2/files/meta", query_string=payload, headers=headers)
    assert response.status_code == 403


def test_list_meta_bad_zone_400(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    mock_data = {
        "result": [
            MOCK_FILE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/search", json=mock_data)

    mock_data = {
        "result": MOCK_FILE_DATA
    }
    file_id = MOCK_FILE_DATA["parent"]
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f"item/{file_id}", json=mock_data)

    payload = {
        "zone": "bad",
        "source_type": "folder",
        "parent_path": MOCK_FILE_DATA["parent_path"],
        "project_code": "test_project"
    }
    headers = {"Authorization": jwt_token_admin}
    response = test_client.get("v2/files/meta", query_string=payload, headers=headers)
    assert response.status_code == 400


def test_list_meta_bad_source_type_400(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    mock_data = {
        "result": [
            MOCK_FILE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/search", json=mock_data)

    mock_data = {
        "result": MOCK_FILE_DATA
    }
    file_id = MOCK_FILE_DATA["parent"]
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f"item/{file_id}", json=mock_data)

    payload = {
        "zone": "greenroom",
        "source_type": "bad",
        "parent_path": MOCK_FILE_DATA["parent_path"],
        "project_code": "test_project"
    }
    headers = {"Authorization": jwt_token_admin}
    response = test_client.get("v2/files/meta", query_string=payload, headers=headers)
    assert response.status_code == 400


def test_list_meta_filter_200(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    mock_data = {
        "result": [
            MOCK_FILE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/search", json=mock_data)

    mock_data = {
        "result": MOCK_FILE_DATA
    }
    file_id = MOCK_FILE_DATA["parent"]
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f"item/{file_id}", json=mock_data)

    payload = {
        "zone": "greenroom",
        "source_type": "folder",
        "parent_path": MOCK_FILE_DATA["parent_path"],
        "project_code": "test_project",
        "name": "test%",
        "owner": "test%",
    }
    headers = {"Authorization": jwt_token_admin}
    response = test_client.get("v2/files/meta", query_string=payload, headers=headers)
    assert response.status_code == 200


def test_list_meta_trash_200(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    mock_data = {
        "result": [
            MOCK_FILE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/search", json=mock_data)

    mock_data = {
        "result": MOCK_FILE_DATA
    }
    file_id = MOCK_FILE_DATA["parent"]
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f"item/{file_id}", json=mock_data)

    payload = {
        "zone": "greenroom",
        "source_type": "trash",
        "parent_path": MOCK_FILE_DATA["parent_path"],
        "project_code": "test_project",
    }
    headers = {"Authorization": jwt_token_admin}
    response = test_client.get("v2/files/meta", query_string=payload, headers=headers)
    assert response.status_code == 200


def test_file_detail_bulk_200(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    mock_data = {
        "result": [
            MOCK_FILE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/batch", json=mock_data)

    payload = {
        "ids": [MOCK_FILE_DATA["id"]]
    }
    headers = {"Authorization": jwt_token_admin}
    response = test_client.post("v2/files/bulk/detail", json=payload, headers=headers)
    assert response.status_code == 200


def test_file_detail_bulk_permissions_403(test_client, requests_mocker, jwt_token_contrib, has_permission_false):
    mock_data = {
        "result": [
            MOCK_FILE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/batch", json=mock_data)

    payload = {
        "ids": [MOCK_FILE_DATA["id"]]
    }
    headers = {"Authorization": jwt_token_contrib}
    response = test_client.post("v2/files/bulk/detail", json=payload, headers=headers)
    assert response.status_code == 403
