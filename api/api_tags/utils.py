from models.api_response import EAPIResponseCode
from resources.error_handler import APIException
from services.permissions_service.utils import get_project_role, has_permission


def check_tag_permissions(entity: dict, username: str):
    name_folder = entity["parent_path"].split(".")[0]

    if entity["zone"] == 1:
        zone = 'greenroom'
    else:
        zone = 'core'

    if not has_permission(entity["container_code"], 'tags', zone, 'create'):
        raise APIException(error_msg="Permission Denied", status_code=EAPIResponseCode.forbidden.value)

    role = get_project_role(entity["container_code"])
    if role == "contributor" and username != name_folder:
        raise APIException(error_msg="Permission Denied", status_code=EAPIResponseCode.forbidden.value)
    if role == "collaborator" and zone != "core" and username != name_folder:
        raise APIException(error_msg="Permission Denied", status_code=EAPIResponseCode.forbidden.value)


def get_new_tags(operation: str, entity: dict, new_tags: list):
    if operation == "add":
        new_tags = entity["extended"]["extra"]["tags"] + new_tags
    else:
        new_tags = [i for i in entity["extended"]["extra"]["tags"] if i not in new_tags]
    return list(set(new_tags))
