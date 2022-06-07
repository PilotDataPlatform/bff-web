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


def test_update_tags_200(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    entity_id = MOCK_FILE_DATA["id"]
    mock_data = {
        "result": MOCK_FILE_DATA
    }
    requests_mocker.put(ConfigClass.METADATA_SERVICE + "item?id=" + entity_id, json=mock_data)

    mock_data = {
        "result": MOCK_FILE_DATA
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f"item/{entity_id}", json=mock_data)

    payload = {
        "tags": [
            "tag3"
        ],
    }
    headers = {"Authorization": jwt_token_admin}
    response = test_client.post(f"v2/{entity_id}/tags", json=payload, headers=headers)
    assert response.status_code == 200


def test_update_tags_bad_type_400(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    entity_id = MOCK_FILE_DATA["id"]
    mock_data = {
        "result": MOCK_FILE_DATA
    }
    requests_mocker.put(ConfigClass.METADATA_SERVICE + "item?id=" + entity_id, json=mock_data)

    mock_data = {
        "result": MOCK_FILE_DATA
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + f"item/{entity_id}", json=mock_data)

    payload = {
        "tags": "tag3"
    }
    headers = {"Authorization": jwt_token_admin}
    response = test_client.post(f"v2/{entity_id}/tags", json=payload, headers=headers)
    assert response.status_code == 400
