"""Folder creation API."""
import httpx
from common import LoggerFactory
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource

from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from services.meta import get_entity_by_id
from services.permissions_service.decorators import permissions_check

_logger = LoggerFactory('api_folder_creation').get_logger()


class FolderCreation(Resource):
    _logger = LoggerFactory('api_folder_creation').get_logger()

    @jwt_required()
    @permissions_check('file', '*', 'upload')
    def post(self, project_id):
        api_response = APIResponse()
        data = request.get_json()
        folder_name = data.get("folder_name")
        project_code = data.get("project_code")
        zone = data.get("zone")
        destination_id = data.get("destination_id")
        parent_entity = None
        entity_type = "folder"
        if destination_id:
            try:
                parent_entity = get_entity_by_id(destination_id)
            except Exception:
                # name folder
                entity_type = "name_folder"

        if len(folder_name) < 1 or len(folder_name) > 20:
            api_response.set_code(EAPIResponseCode.bad_request)
            api_response.set_error_msg("Folder should be 1 to 20 characters")
            return api_response.to_dict, api_response.code

        payload = {
            "name": folder_name,
            "zone": 0 if zone == "greenroom" else 1,
            "type": entity_type,
            "owner": current_identity["username"],
            "container_code": project_code,
            "container_type": "project",
            "size": 0,
            "location_uri": "",
            "version": "",
        }
        if parent_entity:
            payload["parent"] = parent_entity["id"]
            if parent_entity.get("parent_path"):
                payload["parent_path"] = parent_entity["parent_path"] + "." + parent_entity["name"]
            else:
                # name folder
                payload["parent_path"] = parent_entity["name"]

        with httpx.Client() as client:
            response = client.post(ConfigClass.METADATA_SERVICE + "item/", json=payload)
        return response.json(), response.status_code
