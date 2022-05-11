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

