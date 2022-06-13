import requests
from flask_jwt import current_identity

from config import ConfigClass
from services.permissions_service.utils import get_project_role


def is_greenroom(file_node):
    if file_node["zone"] == 1:
        return False
    else:
        return True


def has_permissions(template_id, file_node):
    try:
        response = requests.get(ConfigClass.METADATA_SERVICE + f'template/{template_id}/')
        manifest = response.json()['result']
        if not manifest:
            return False
    except Exception as e:
        error_msg = {"result": str(e)}
        return error_msg, 500

    if current_identity["role"] != "admin":
        role = get_project_role(manifest['project_code'])
        if role == "contributor":
            # contrib must own the file to attach manifests
            root_folder = file_node["parent_path"].split(".")[0]
            if root_folder != current_identity["username"]:
                return False
        elif role == "collaborator":
            if is_greenroom(file_node):
                root_folder = file_node["parent_path"].split(".")[0]
                if root_folder != current_identity["username"]:
                    return False
    return True
