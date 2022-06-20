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
