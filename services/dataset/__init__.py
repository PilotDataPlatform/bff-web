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
