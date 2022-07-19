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

from typing import Any
from typing import Dict
from typing import Mapping

from common import LoggerFactory
from fastapi import Depends
from httpx import AsyncClient
from httpx import Response

from config import Settings
from config import get_settings

logger = LoggerFactory('search_client').get_logger()


class SearchServiceException(Exception):
    """Raised when any unexpected behaviour occurred while querying search service."""


class SearchServiceClient:
    """Client for search service."""

    def __init__(self, endpoint: str) -> None:
        self.endpoint_v1 = f'{endpoint}/v1'
        self.client = AsyncClient(timeout=30)

    async def _get(self, url: str, params: Mapping[str, Any]) -> Response:
        logger.info(f'Calling search service {url} with query params: {params}')

        try:
            response = await self.client.get(url, params=params)
            assert response.is_success
        except Exception:
            message = f'Unable to query data from search service with url "{url}" and params "{params}".'
            logger.exception(message)
            raise SearchServiceException(message)

        return response

    async def get_metadata_items(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Query metadata items."""

        url = self.endpoint_v1 + '/metadata-items/'
        response = await self._get(url, params)

        return response.json()

    async def get_dataset_activity_logs(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Query dataset activity logs."""

        url = self.endpoint_v1 + '/dataset-activity-logs/'
        response = await self._get(url, params)

        return response.json()

    async def get_project_size(self, project_code: str, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Get storage usage for a project."""

        url = self.endpoint_v1 + f'/project-files/{project_code}/size'
        response = await self._get(url, params)

        return response.json()

    async def get_project_statistics(self, project_code: str, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Get files and transfer activity statistics for a project."""

        url = self.endpoint_v1 + f'/project-files/{project_code}/statistics'
        response = await self._get(url, params)

        return response.json()

    async def get_project_activity(self, project_code: str, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Get file activity statistic for a project."""

        url = self.endpoint_v1 + f'/project-files/{project_code}/activity'
        response = await self._get(url, params)

        return response.json()


def get_search_service_client(settings: Settings = Depends(get_settings)) -> SearchServiceClient:
    """Get search service client as a FastAPI dependency."""

    return SearchServiceClient(settings.SEARCH_SERVICE)
