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
from models.api_response import EAPIResponseCode
from resources.error_handler import APIException
import requests


def get_entity_by_id(entity_id: str) -> dict:
    response = requests.get(ConfigClass.METADATA_SERVICE + f'item/{entity_id}')
    if response.status_code != 200:
        error_msg = f'Error calling Meta service get_node_by_id: {response.json()}'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    if not response.json()['result']:
        error_msg = 'Entity not found'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.not_found.value)
    return response.json()['result']


def get_entities_batch(entity_ids: list) -> list:
    response = requests.get(ConfigClass.METADATA_SERVICE + "items/batch", params={"ids": entity_ids})
    if response.status_code != 200:
        error_msg = f'Error calling Meta service get_node_by_id: {response.json()}'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    return response.json()['result']


def search_entities(
    container_code: str,
    parent_path: str,
    zone: str,
    recursive: bool = False,
    name: str = "",
) -> list:
    payload = {
        "container_code": container_code,
        "parent_path": parent_path,
        "zone": zone,
        "recursive": recursive,
    }
    if name:
        payload["name"] = name
    response = requests.get(ConfigClass.METADATA_SERVICE + "items/search", params=payload)
    if response.status_code != 200:
        error_msg = f'Error calling Meta service search_entities: {response.json()}'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    return response.json()['result']
