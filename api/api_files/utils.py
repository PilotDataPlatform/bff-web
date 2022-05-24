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
        raise APIException(status_code=EAPIResponseCode.not_found,
                           error_msg=f'Collection {collection_geid} does not exist')
