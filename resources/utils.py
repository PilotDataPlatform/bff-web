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
import datetime
from datetime import timezone

import httpx
import requests

from config import ConfigClass
from services.permissions_service.utils import has_permission


def check_invite_permissions(dataset_node, current_identity):
    if not dataset_node:
        # Only platform admin can invite without a project
        if current_identity['role'] != 'admin':
            return False
    if current_identity['role'] != 'admin':
        if not has_permission(dataset_node['code'], 'invite', '*', 'create', current_identity):
            return False
    return True


def remove_user_from_project_group(project_code, user_email, logger):
    # Remove user from keycloak group with the same name as the project
    payload = {
        'operation_type': 'remove',
        'user_email': user_email,
        'group_code': project_code,
    }
    res = requests.put(
        url=ConfigClass.AUTH_SERVICE + 'user/ad-group',
        json=payload,
    )
    if res.status_code != 200:
        logger.error(f'Error removing user from group in ad: {res.text} {res.status_code}')


def add_user_to_ad_group(user_email, project_code, logger):
    payload = {
        'operation_type': 'add',
        'user_email': user_email,
        'group_code': project_code,
    }
    res = requests.put(
        url=ConfigClass.AUTH_SERVICE + 'user/ad-group',
        json=payload,
    )
    if res.status_code != 200:
        logger.error(f'Error adding user to group in ad: {res.text} {res.status_code}')

    return res.json().get('entry')


# Simple Helpers #


def helper_now_utc():
    dt = datetime.datetime.now()
    utc_time = dt.replace(tzinfo=timezone.utc)
    return utc_time


def get_dataset(dataset_id: str) -> dict:
    response = requests.get(f'{ConfigClass.DATASET_SERVICE}dataset/{dataset_id}')
    res = response.json()
    dataset = res['result']
    return dataset


async def get_dataset_by_code(dataset_code: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f'{ConfigClass.DATASET_SERVICE}dataset-peek/{dataset_code}')
    res = response.json()
    dataset = res['result']
    return dataset
