from flask_jwt import current_identity
import requests
from config import ConfigClass
from .utils import has_permission, get_project_code_from_request
from common import LoggerFactory

_logger = LoggerFactory('permissions').get_logger()

def permissions_check(resource, zone, operation):
    def inner(function):
        def wrapper(*args, **kwargs):
            project_code = get_project_code_from_request(kwargs)
            if not project_code:
                _logger.error("Couldn't get project_code in permissions_check decorator")
            if has_permission(project_code, resource, zone, operation):
                return function(*args, **kwargs)
            _logger.info(f"Permission denied for {project_code} - {resource} - {zone} - {operation}")
            return {'result': 'Permission Denied', 'error_msg': 'Permission Denied'}, 403
        return wrapper
    return inner

# this is temperory function to check the operation
# on the dataset. Any post/put action will ONLY require the owner
def dataset_permission():
    def inner(function):
        def wrapper(*args, **kwargs):
            dateset_geid = kwargs.get("dataset_geid")

            # here we have to find the parent node and delete the relationship
            query_url = ConfigClass.NEO4J_SERVICE + "nodes/Dataset/query"
            query_payload = {
                "global_entity_id": dateset_geid,
                "creator": current_identity.get("username"),
            }
            response = requests.post(query_url, json=query_payload)

            # if not the owner and not the platform admin
            if len(response.json()) == 0:
                return {'result': 'Permission Denied', 'error_msg': 'Permission Denied'}, 403

            return function(*args, **kwargs)
        return wrapper
    return inner

# this is temperory function to check the operation
# on the dataset. Any post/put action will ONLY require the owner
def dataset_permission_bycode():
    def inner(function):
        def wrapper(*args, **kwargs):
            dataset_code = kwargs.get("dataset_code")

            # here we have to find the parent node and delete the relationship
            query_url = ConfigClass.NEO4J_SERVICE + "nodes/Dataset/query"
            query_payload = {
                "code": dataset_code,
                "creator": current_identity.get("username"),
            }
            response = requests.post(query_url, json=query_payload)
            # print(response.json())

            # if not the owner and not the platform admin
            if len(response.json()) == 0:
                return {'result': 'Permission Denied', 'error_msg': 'Permission Denied'}, 403

            return function(*args, **kwargs)

        return wrapper
    return inner

