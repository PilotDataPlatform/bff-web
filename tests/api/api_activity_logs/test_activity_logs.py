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

from uuid import uuid4

import pytest

from config import ConfigClass

MOCK_DATASET = {
    'result': {
        'creator': 'test',
        'code': 'testprojectdev',
    }
}


MOCK_FOREIGN_DATASET = {
    'result': {
        'creator': 'another_user',
        'code': 'testprojectdev',
    }
}

MOCK_NO_DATASET = {'result': {}}


@pytest.mark.asyncio
async def test_get_activity_logs_admin_200(test_client, requests_mocker, jwt_token_admin):
    dataset_id = str(uuid4())
    requests_mocker.get(f'{ConfigClass.DATASET_SERVICE}dataset/{dataset_id}', json=MOCK_DATASET)
    requests_mocker.get(ConfigClass.SEARCH_SERVICE + 'dataset-activity-logs/')
    headers = {'Authorization': jwt_token_admin}

    response = test_client.get(f'/v1/activity-logs/{dataset_id}', headers=headers)
    assert response.status_code == 200


def test_get_activity_logs_contrib_200(test_client, requests_mocker, jwt_token_contrib):
    dataset_id = str(uuid4())
    requests_mocker.get(f'{ConfigClass.DATASET_SERVICE}dataset/{dataset_id}', json=MOCK_DATASET)
    requests_mocker.get(ConfigClass.SEARCH_SERVICE + 'dataset-activity-logs/')
    headers = {'Authorization': jwt_token_contrib}

    response = test_client.get(f'/v1/activity-logs/{dataset_id}', headers=headers)
    assert response.status_code == 200


def test_get_activity_logs_contrib_403_no_permission(test_client, requests_mocker, jwt_token_contrib):
    dataset_id = str(uuid4())
    requests_mocker.get(f'{ConfigClass.DATASET_SERVICE}dataset/{dataset_id}', json=MOCK_FOREIGN_DATASET)
    requests_mocker.get(ConfigClass.SEARCH_SERVICE + 'dataset-activity-logs/')
    headers = {'Authorization': jwt_token_contrib}

    response = test_client.get(f'/v1/activity-logs/{dataset_id}', headers=headers)
    assert response.status_code == 403
    assert response.json()['result'] == 'No permission for this dataset'


def test_get_activity_logs_contrib_403_wrong_dataset_id(test_client, requests_mocker, jwt_token_contrib):
    dataset_id = str(uuid4())
    requests_mocker.get(f'{ConfigClass.DATASET_SERVICE}dataset/{dataset_id}', json=MOCK_NO_DATASET)
    requests_mocker.get(ConfigClass.SEARCH_SERVICE + 'dataset-activity-logs/')
    headers = {'Authorization': jwt_token_contrib}

    response = test_client.get(f'/v1/activity-logs/{dataset_id}', headers=headers)
    assert response.status_code == 400
    assert response.json()['result'] == 'Dataset does not exist'
