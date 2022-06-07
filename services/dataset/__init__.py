from config import ConfigClass
from models.api_response import EAPIResponseCode
from resources.error_handler import APIException
import requests


def get_dataset_by_id(dataset_id: str) -> dict:
    response = requests.get(ConfigClass.DATASET_SERVICE + f'dataset/{dataset_id}')
    print(response.json())
    if response.status_code != 200:
        error_msg = f'Error calling Dataset service get_dataset_by_id: {response.json()}'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    if not response.json()['result']:
        error_msg = 'Dataset not found'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.not_found.value)
    return response.json()['result']


def get_dataset_by_code(dataset_code: str) -> dict:
    response = requests.get(ConfigClass.DATASET_SERVICE + f'dataset-peek/{dataset_code}')
    if response.status_code != 200:
        error_msg = f'Error calling Dataset service get_dataset_by_code: {response.json()}'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.internal_error.value)
    if not response.json()['result']:
        error_msg = 'Dataset not found'
        raise APIException(error_msg=error_msg, status_code=EAPIResponseCode.not_found.value)
    return response.json()['result']
