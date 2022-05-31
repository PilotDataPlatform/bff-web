from models.api_response import APIResponse, EAPIResponseCode
from config import ConfigClass
from flask_jwt import current_identity
from services.dataset import get_dataset_by_id


def check_dataset_permissions(dataset_id):
    api_response = APIResponse()
    dataset_node = get_dataset_by_id(dataset_id)

    if dataset_node["creator"] != current_identity["username"]:
        api_response.set_code(EAPIResponseCode.forbidden)
        api_response.set_result("Permission Denied")
        return False, api_response
    return True, None
