import json
from flask_jwt import current_identity
from config import ConfigClass
import requests
from resources.error_handler import APIException
from models.api_response import EAPIResponseCode

def check_folder_permissions(folder_node):
    if folder_node["folder_relative_path"]:
        root_folder = folder_node["folder_relative_path"].split("/")[0]
    else:
        root_folder = folder_node["name"]
    if root_folder != current_identity["username"]:
        return False
    return True


def parse_json(data):
    try:
        return json.loads(data)
    except Exception as e:
        return False


def get_collection_by_id(collection_geid):
    url = f'{ConfigClass.METADATA_SERVICE}collection/{collection_geid}/'
    response = requests.get(url)
    res = response.json()['result']
    if res:
        return res
    else:
        raise APIException(status_code=EAPIResponseCode.not_found,
                           error_msg=f'Collection {collection_geid} does not exist')
