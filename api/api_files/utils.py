import json
from flask_jwt import current_identity


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

