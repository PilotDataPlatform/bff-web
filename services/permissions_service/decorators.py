from flask import request
from flask_jwt import current_identity
import requests
from config import ConfigClass
from .utils import has_permission, get_project_code_from_request
from services.logger_services.logger_factory_service import SrvLoggerFactory
from services.neo4j_service.neo4j_client import Neo4jClient

_logger = SrvLoggerFactory('permissions').get_logger()

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
            relation_query_url = ConfigClass.NEO4J_SERVICE + "relations/query"
            query_payload = {
                "label": "own",
                "end_label": "Dataset",
                "end_params": {"global_entity_id":dateset_geid},
                "start_label": "User",
                "start_params": {"name":current_identity.get("username")},
            }
            response = requests.post(relation_query_url, json=query_payload)

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
            # print(args)
            # print(kwargs)
            dataset_code = kwargs.get("dataset_code")

            # here we have to find the parent node and delete the relationship
            relation_query_url = ConfigClass.NEO4J_SERVICE + "relations/query"
            query_payload = {
                "label": "own",
                "end_label": "Dataset",
                "end_params": {"code": dataset_code},
                "start_label": "User",
                "start_params": {"name":current_identity.get("username")},
            }
            response = requests.post(relation_query_url, json=query_payload)
            # print(response.json())

            # if not the owner and not the platform admin
            if len(response.json()) == 0:
                return {'result': 'Permission Denied', 'error_msg': 'Permission Denied'}, 403

            return function(*args, **kwargs)
            
        return wrapper
    return inner
