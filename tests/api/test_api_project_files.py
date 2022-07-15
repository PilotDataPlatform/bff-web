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

import os
import re
from typing import Union

import pytest

from config import ConfigClass


@pytest.fixture
def mock_project():
    def _mock_project(project_code: str):
        return {
            'code': project_code,
        }

    yield _mock_project


@pytest.fixture
def mock_metadata_item():
    def _mock_metadata_item(zone: Union[int, str]):
        return {
            'zone': zone,
        }

    yield _mock_metadata_item


@pytest.mark.asyncio
async def test_search_replaces_zone_numbers_with_string_values(
    mocker, test_async_client, httpx_mock, mock_project, mock_metadata_item
):
    mocker.patch('app.auth.get_current_identity', return_value={'role': 'admin'})
    project_code = os.urandom(6).hex()
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.PROJECT_SERVICE}/v1/projects/{project_code}',
        json=mock_project(project_code),
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/metadata-items/.*?container_code={project_code}.*$'),
        json={
            'total_per_zone': {0: 10, 1: 20, 2: 30},
            'result': [mock_metadata_item(0), mock_metadata_item(1), mock_metadata_item(2)],
        },
    )
    expected_response = {
        'total_per_zone': {
            ConfigClass.GREENROOM_ZONE_LABEL: 10,
            ConfigClass.CORE_ZONE_LABEL: 20,
            '2': 30,
        },
        'result': [
            mock_metadata_item(ConfigClass.GREENROOM_ZONE_LABEL),
            mock_metadata_item(ConfigClass.CORE_ZONE_LABEL),
            mock_metadata_item('2'),
        ],
    }
    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project_code}/search', headers=headers)

    assert response.status_code == 200

    assert response.json() == expected_response


@pytest.mark.asyncio
async def test_size_endpoint_returns_search_service_response(
    mocker, test_async_client, httpx_mock, mock_project, mock_metadata_item
):
    mocker.patch('app.auth.get_current_identity', return_value={'role': 'member'})
    project_code = os.urandom(6).hex()
    expected_response = {
        'data': {
            'labels': ['2022-01', '2022-02', '2022-03'],
            'datasets': [
                {'label': 0, 'values': [536870912, 715827882, 920350134]},
                {'label': 1, 'values': [107374182, 143165576, 184070026]},
            ],
        }
    }
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.PROJECT_SERVICE}/v1/projects/{project_code}',
        json=mock_project(project_code),
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project_code}/size'),
        json=expected_response,
    )
    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project_code}/size', headers=headers)

    assert response.status_code == 200

    assert response.json() == expected_response


@pytest.mark.asyncio
async def test_statistics_endpoint_returns_search_service_response(mocker, test_async_client, httpx_mock, mock_project):
    mocker.patch('app.auth.get_current_identity', return_value={'role': 'member'})
    project_code = os.urandom(6).hex()
    expected_response = {
        'files': {'total_count': 1, 'total_size': 1},
        'activity': {'today_uploaded': 2, 'today_downloaded': 2},
    }
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.PROJECT_SERVICE}/v1/projects/{project_code}',
        json=mock_project(project_code),
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project_code}/statistics'),
        json=expected_response,
    )
    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project_code}/statistics', headers=headers)

    assert response.status_code == 200

    assert response.json() == expected_response


@pytest.mark.asyncio
async def test_activity_endpoint_returns_search_service_response(mocker, test_async_client, httpx_mock, mock_project):
    mocker.patch('app.auth.get_current_identity', return_value={'role': 'member'})
    project_code = os.urandom(6).hex()
    expected_response = {
        'data': {
            '2022-01-01': 1,
            '2022-01-02': 0,
            '2022-01-03': 10,
        }
    }
    httpx_mock.add_response(
        method='GET',
        url=f'{ConfigClass.PROJECT_SERVICE}/v1/projects/{project_code}',
        json=mock_project(project_code),
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile(rf'^{ConfigClass.SEARCH_SERVICE}/v1/project-files/{project_code}/activity'),
        json=expected_response,
    )
    headers = {'Authorization': ''}
    response = await test_async_client.get(f'/v1/project-files/{project_code}/activity', headers=headers)

    assert response.status_code == 200

    assert response.json() == expected_response
