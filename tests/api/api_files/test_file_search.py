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
async def test_get_files_search_replaces_zone_numbers_with_string_values(
    mocker, test_async_client, httpx_mock, mock_project, mock_metadata_item
):
    project_code = os.urandom(6).hex()
    mocker.patch('app.auth.get_current_identity', return_value={'role': 'admin'})
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
    response = await test_async_client.get(f'/v1/{project_code}/files/search', headers=headers)

    assert response.status_code == 200

    assert response.json() == expected_response
