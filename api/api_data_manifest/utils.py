# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import requests

from config import ConfigClass
from services.permissions_service.utils import get_project_role


def has_permissions(template_id, file_node, current_identity):
    try:
        response = requests.get(ConfigClass.METADATA_SERVICE + f'template/{template_id}/')
        manifest = response.json()['result']
        if not manifest:
            return False
    except Exception as e:
        error_msg = {"result": str(e)}
        return error_msg, 500

    if current_identity["role"] != "admin":
        role = get_project_role(manifest['project_code'], current_identity)
        if role == "contributor":
            # contrib must own the file to attach manifests
            root_folder = file_node["parent_path"].split(".")[0]
            if root_folder != current_identity["username"]:
                return False
        elif role == "collaborator":
            if file_node["zone"] == 0:
                root_folder = file_node["parent_path"].split(".")[0]
                if root_folder != current_identity["username"]:
                    return False
    return True
