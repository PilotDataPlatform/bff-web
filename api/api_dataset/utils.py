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
from flask_jwt import current_identity

from config import ConfigClass
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from services.dataset import get_dataset_by_id


def check_dataset_permissions(dataset_id):
    api_response = APIResponse()
    dataset_node = get_dataset_by_id(dataset_id)

    if dataset_node['creator'] != current_identity['username']:
        api_response.set_code(EAPIResponseCode.forbidden)
        api_response.set_result('Permission Denied')
        return False, api_response
    return True, None
