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
    mock_data = {
        "result": [
            MOCK_FILE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/search", json=mock_data)

    mock_data = {
        "result": [MOCK_FILE_DATA]
    }
    matcher = re.compile(ConfigClass.METADATA_SERVICE + 'items/batch.*')
    requests_mocker.get(matcher, json=mock_data)

    mock_data = {
        "result": [MOCK_FILE_DATA]
    }
    requests_mocker.put(ConfigClass.METADATA_SERVICE + 'items/batch', json=mock_data)

    payload = {
        "entity": [
            MOCK_FILE_DATA["id"],
        ],
        "project_geid": str(uuid4()),
        "tags": [
            "tag3"
        ],
        "only_files": True,
        "operation": "add",
        "inherit": True
    }
    headers = {"Authorization": jwt_token_admin}
    response = test_client.post("v2/entity/tags", json=payload, headers=headers)
    assert response.status_code == 200


def test_update_tags_inherit_200(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    mock_data = {
        "result": [
            MOCK_FILE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/search", json=mock_data)

    mock_data = {
        "result": [MOCK_FILE_DATA]
    }
    matcher = re.compile(ConfigClass.METADATA_SERVICE + 'items/batch.*')
    requests_mocker.get(matcher, json=mock_data)

    mock_data = {
        "result": [MOCK_FILE_DATA]
    }
    requests_mocker.put(ConfigClass.METADATA_SERVICE + 'items/batch', json=mock_data)

    payload = {
        "entity": [
            MOCK_FILE_DATA["id"],
        ],
        "project_geid": str(uuid4()),
        "tags": [
            "tag3"
        ],
        "only_files": False,
        "operation": "add",
        "inherit": True
    }
    headers = {"Authorization": jwt_token_admin}
    response = test_client.post("v2/entity/tags", json=payload, headers=headers)
    assert response.status_code == 200


def test_update_tags_only_files_200(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    mock_folder = MOCK_FILE_DATA.copy()
    mock_folder["type"] = "folder"
    mock_data = {
        "result": [
            mock_folder
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/search", json=mock_data)

    mock_data = {
        "result": [mock_folder]
    }
    matcher = re.compile(ConfigClass.METADATA_SERVICE + 'items/batch.*')
    requests_mocker.get(matcher, json=mock_data)

    mock_data = {
        "result": [mock_folder]
    }
    requests_mocker.put(ConfigClass.METADATA_SERVICE + 'items/batch', json=mock_data)

    payload = {
        "entity": [
            MOCK_FILE_DATA["id"],
        ],
        "project_geid": str(uuid4()),
        "tags": [
            "tag3"
        ],
        "only_files": True,
        "operation": "add",
        "inherit": True
    }
    headers = {"Authorization": jwt_token_admin}
    response = test_client.post("v2/entity/tags", json=payload, headers=headers)
    assert response.status_code == 200


def test_update_tags_remove_200(test_client, requests_mocker, jwt_token_admin, has_permission_true):
    mock_data = {
        "result": [
            MOCK_FILE_DATA
        ]
    }
    requests_mocker.get(ConfigClass.METADATA_SERVICE + "items/search", json=mock_data)

    mock_data = {
        "result": [MOCK_FILE_DATA]
    }
    matcher = re.compile(ConfigClass.METADATA_SERVICE + 'items/batch.*')
    requests_mocker.get(matcher, json=mock_data)

    mock_data = {
        "result": [MOCK_FILE_DATA]
    }
    requests_mocker.put(ConfigClass.METADATA_SERVICE + 'items/batch', json=mock_data)

    payload = {
        "entity": [
            MOCK_FILE_DATA["id"],
        ],
        "project_geid": str(uuid4()),
        "tags": [
            "tag3"
        ],
        "only_files": False,
        "operation": "remove",
        "inherit": True
    }
    headers = {"Authorization": jwt_token_admin}
    response = test_client.post("v2/entity/tags", json=payload, headers=headers)
    assert response.status_code == 200
