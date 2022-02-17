from flask_jwt import current_identity
from flask import request
import requests
from services.logger_services.logger_factory_service import SrvLoggerFactory
from services.neo4j_service.neo4j_client import Neo4jClient
from config import ConfigClass

_logger = SrvLoggerFactory('permissions').get_logger()


def has_permission(project_code, resource, zone, operation):
    if current_identity["role"] == "admin":
        role = "platform_admin"
    else:
        if not project_code:
            _logger.info(
                f"No project code and not a platform admin, permission denied")
            return False
        role = get_project_role(project_code)
        if not role:
            _logger.info(
                f"Unable to get project role in permissions check, user might not belong to project")
            return False

    try:
        payload = {
            "role": role,
            "resource": resource,
            "zone": zone,
            "operation": operation,
        }
        response = requests.get(
            ConfigClass.AUTH_SERVICE + "authorize", params=payload)
        if response.status_code != 200:
            raise Exception(f"Error calling authorize API - {response.json()}")
        if response.json()["result"].get("has_permission"):
            return True
        else:
            return False
    except Exception as e:
        error_msg = str(e)
        _logger.info(f"Exception on authorize call: {error_msg}")
        raise Exception(f"Error calling authorize API - {error_msg}")


def get_project_role(project_code):
    role = None
    if current_identity["role"] == "admin":
        role = "platform_admin"
    else:
        possible_roles = [project_code + "-" +
                          i for i in ["admin", "contributor", "collaborator"]]
        for realm_role in current_identity["realm_roles"]:
            # if this is a role for the correct project
            if realm_role in possible_roles:
                role = realm_role.replace(project_code + "-", "")
    return role


def get_project_code_from_request(kwargs):
    if request.method == "POST":
        data = request.get_json()
    else:
        data = request.args

    if "project_code" in data:
        return data["project_code"]
    if "project_geid" in data:
        client = Neo4jClient()
        result = client.get_container_by_geid(data["project_geid"])
        if result.get("code") != 200:
            error_msg = result.get("error_msg")
            _logger.error(
                f"Couldn't get project in permissions check - {error_msg}")
            return False
        project = result.get("result")
        return project["code"]
    if "container_id" in data:
        client = Neo4jClient()
        result = client.node_get("Container", data["container_id"])
        if result.get("code") != 200:
            error_msg = result.get("error_msg")
            _logger.error(
                f"Couldn't get project in permissions check - {error_msg}")
            return False
        project = result.get("result")
        return project["code"]
    if "project_geid" in kwargs:
        client = Neo4jClient()
        result = client.get_container_by_geid(kwargs["project_geid"])
        if result.get("code") != 200:
            error_msg = result.get("error_msg")
            _logger.error(
                f"Couldn't get project in permissions check - {error_msg}")
            return False
        project = result.get("result")
        return project["code"]
    if "dataset_id" in kwargs:
        client = Neo4jClient()
        result = client.node_get("Container", kwargs["dataset_id"])
        if result.get("code") != 200:
            error_msg = result.get("error_msg")
            _logger.error(
                f"Couldn't get project in permissions check - {error_msg}")
            return False
        project = result.get("result")
        return project["code"]
