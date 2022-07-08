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
async def test_get_activity_logs_admin_200(test_async_client, httpx_mock, mocker):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'test'})
    dataset_code = 'testprojectdev'
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}dataset-peek/{dataset_code}',
        json=MOCK_DATASET,
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}dataset-activity-logs/.*?container_code={dataset_code}.*$'),
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/activity-logs/{dataset_code}', headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_activity_logs_contrib_200(test_async_client, httpx_mock, mocker):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'test'})
    dataset_code = 'testprojectdev'
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}dataset-peek/{dataset_code}',
        json=MOCK_DATASET,
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}dataset-activity-logs/.*?container_code={dataset_code}.*$'),
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/activity-logs/{dataset_code}', headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_activity_logs_contrib_403_no_permission(test_async_client, httpx_mock, mocker):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'test'})
    dataset_code = 'testprojectdev'
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}dataset-peek/{dataset_code}',
        json=MOCK_FOREIGN_DATASET,
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/activity-logs/{dataset_code}', headers=headers)
    assert response.status_code == 403
    assert response.json()['result'] == 'No permission for this dataset'


@pytest.mark.asyncio
async def test_get_activity_logs_contrib_403_wrong_dataset_code(test_async_client, httpx_mock, mocker):
    mocker.patch('app.auth.get_current_identity', return_value={'username': 'test'})
    dataset_code = 'testprojectdev'
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.DATASET_SERVICE}dataset-peek/{dataset_code}',
        json=MOCK_NO_DATASET,
    )
    headers = {'Authorization': ''}

    response = await test_async_client.get(f'/v1/activity-logs/{dataset_code}', headers=headers)
    assert response.status_code == 400
    assert response.json()['result'] == 'Dataset does not exist'
