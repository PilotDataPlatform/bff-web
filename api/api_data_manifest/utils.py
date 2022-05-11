import re

import requests
from flask_jwt import current_identity

from config import ConfigClass
from models.api_data_manifest import DataAttributeModel, DataManifestModel, db
from services.permissions_service.utils import get_project_role


def is_greenroom(file_node):
    if file_node["zone"] == 0:
        return False
    else:
        return True

def has_permissions(manifest_id, file_node):
    manifest = db.session.query(DataManifestModel).get(manifest_id)
    if not manifest:
        return False

    if current_identity["role"] != "admin":
        role = get_project_role(manifest.project_code)
        if role != "admin":
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


def has_valid_attributes(manifest_id, data):
    attributes = db.session.query(DataAttributeModel).filter_by(manifest_id=manifest_id).order_by(DataAttributeModel.id.asc())
    for attr in attributes:
        if not attr.optional and not attr.name in data.get("attributes", {}):
            return False, "Missing required attribute"
        if attr.type.value == "multiple_choice":
            value = data.get("attributes", {}).get(attr.name)
            if value:
                if not value in attr.value.split(","):
                    return False, "Invalid choice field"
            else:
                if not attr.optional:
                    return False, "Field required"
        if attr.type.value == "text":
            value = data.get("attributes", {}).get(attr.name)
            if value:
                if len(value) > 100:
                    return False, "text to long"
            else:
                if not attr.optional:
                    return False, "Field required"
    return True, ""


def check_attributes(attributes):
    # Apply name restrictions
    name_requirements = re.compile("^[a-zA-z0-9]{1,32}$")
    for key, value in attributes.items():
        if not re.search(name_requirements, key):
            return False, "regex validation error"
    return True, ""
