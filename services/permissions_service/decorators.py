from flask_jwt import current_identity
from .utils import has_permission, get_project_code_from_request
from common import LoggerFactory
from services.dataset import get_dataset_by_id, get_dataset_by_code

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
            dataset_id = kwargs.get("dataset_id")
            dataset = get_dataset_by_id(dataset_id)
            if dataset["creator"] != current_identity["username"]:
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
            dataset = get_dataset_by_code(dataset_code)
            if dataset["creator"] != current_identity["username"]:
                return {'result': 'Permission Denied', 'error_msg': 'Permission Denied'}, 403
            return function(*args, **kwargs)

        return wrapper
    return inner

