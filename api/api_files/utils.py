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
import requests
from resources.error_handler import APIException
from models.api_response import EAPIResponseCode


def get_collection_by_id(collection_geid):
    url = f'{ConfigClass.METADATA_SERVICE}collection/{collection_geid}/'
    response = requests.get(url)
    res = response.json()['result']
    if res:
        return res
    else:
        raise APIException(status_code=EAPIResponseCode.not_found.value,
                           error_msg=f'Collection {collection_geid} does not exist')
