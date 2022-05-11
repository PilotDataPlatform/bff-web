"""Folder creation API."""
import os
import re

import httpx
from common import GEIDClient
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource
from common import LoggerFactory

from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from resources.lock import lock_resource, unlock_resource
from resources.swagger_modules import success_return
from services.meta import get_entity_by_id
from services.permissions_service.decorators import permissions_check

from .namespace import datasets_entity_ns

_logger = LoggerFactory('api_folder_creation').get_logger()


class FolderCreationV2(Resource):
    _logger = LoggerFactory('api_folder_creation').get_logger()

    @jwt_required()
    @permissions_check('file', '*', 'upload')
    def post(self, project_geid):
        api_response = APIResponse()
        data = request.get_json()
        folder_name = data.get("folder_name")
        project_code = data.get("project_code")
        zone = data.get("zone")
        destination_id = data.get("destination_id")
        parent_entity = None
        if destination_id:
            parent_entity = get_entity_by_id(destination_id)

        if len(folder_name) < 1 or len(folder_name) > 20:
            api_response.set_code(EAPIResponseCode.bad_request)
            api_response.set_error_msg("Folder should be 1 to 20 characters")
            return api_response.to_dict, api_response.code

        payload = {
            "name": folder_name,
            "zone": 0 if zone == "greenroom" else 1,
            "type": "folder",
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


class FolderCreation(Resource):

    _logger = LoggerFactory('api_folder_creation').get_logger()
    geid_client = GEIDClient()


    @datasets_entity_ns.response(200, success_return)
    @jwt_required()
    @permissions_check('file', '*', 'upload')
    def put(self, project_geid):

        _res = {}

        """create folder / sub folder."""
        request_payload = request.get_json()
        folder_name = request_payload.get("folder_name").strip()

        # check if folder name is valid
        valid = validate_folder_name(folder_name)
        if len(folder_name) < 1 or len(folder_name) > 20 or valid is not None:
            _res.update({"error_msg": "Folder should not contain : (\\/:?*<>|”') and must contain 1 to 20 characters"})
            return _res, 400
        project_code = request_payload.get("project_code")
        zone = request_payload.get("zone")

        destination_geid = request_payload.get("destination_geid")
        global_entity_id = self.geid_client.get_GEID()
        folder_level = 0
        folder_parent_geid = ''
        folder_parent_name = ''
        folder_relative_path = ''
        neo4j_zone_label = ''
        display_path = None

        try:
            # create folder node
            if destination_geid is not None:
                respon_query = get_from_db(destination_geid)
                if respon_query.status_code != 200:
                    error_msg = f'Error while fetching details from db : {respon_query.text}'
                    self._logger.error(error_msg)
                    raise error_msg
                if respon_query.status_code == 200 and len(respon_query.json()) != 0:
                    respon_query = respon_query.json()
                    folder_parent_geid = respon_query[0]['global_entity_id']
                    folder_parent_name = respon_query[0]['name']
                    folder_relative_path = os.path.join(
                        respon_query[0]['folder_relative_path'],
                        folder_parent_name
                    )
                    folder_level = respon_query[0].get('folder_level') + 1
            else:
                error_msg = f'destination {destination_geid} does not exist'
                self._logger.error(error_msg)
                return {"error_msg": error_msg, "result": {}}, 400


            # check if the project exist
            project_query_url = ConfigClass.NEO4J_SERVICE + 'nodes/Container/query'
            payload = {'code': project_code}
            with httpx.Client() as client:
                response = client.post(project_query_url, json=payload)
            if len(response.json()) == 0:
                error_msg = f'project {project_code} does not exist'
                self._logger.error(error_msg)
                return {"error_msg": error_msg, "result": {}}, 400


            # now we have to use the neo4j to check duplicate
            display_path = folder_relative_path + '/' + folder_name if folder_relative_path else folder_name
            payload = {
                'display_path': display_path,
                'project_code': project_code,
                'archived': False,
            }
            # also check if it is in greeroom or core
            neo4j_zone_label = ConfigClass.GREEN_ZONE_LABEL if zone == 'greenroom' else ConfigClass.CORE_ZONE_LABEL
            node_query_url = ConfigClass.NEO4J_SERVICE + 'nodes/%s/query' % neo4j_zone_label
            with httpx.Client() as client:
                response = client.post(node_query_url, json=payload)
            if len(response.json()) > 0:
                error_msg = f'Folder with name {folder_name} already exists in the destination {display_path}'
                self._logger.error(error_msg)
                return {"error_msg": error_msg, "result": {}}, 409

            # formulate the folder metadata
            query = {
                'global_entity_id': global_entity_id,
                'folder_name': folder_name,
                'folder_level': folder_level,
                'folder_parent_geid': folder_parent_geid,
                'folder_parent_name': folder_parent_name,
                'uploader': request_payload.get("uploader"),
                'folder_relative_path': folder_relative_path,
                'zone': neo4j_zone_label,
                'project_code': project_code,
                'folder_tags': request_payload.get("tags"),
                'extra_attrs': {
                    'display_path': display_path,
                },
            }

            # TODO decorator here?
            # before the creation check if folder is on locked
            # this purpose is to avoid racing in the two client
            bucket_prefix = 'gr-' if neo4j_zone_label == ConfigClass.GREEN_ZONE_LABEL else 'core-'
            folder_key = '%s/%s' % (bucket_prefix + project_code, display_path)
            lock_resource(folder_key, 'write')

            query_response = None
            try:
                query_response = create_folder_node(query_params=query)
            except Exception as e:
                raise e
            finally:
                # at the end unlock the folder
                unlock_resource(folder_key, 'write')

            return {"result": query}, 200

        except Exception as error:
            error_msg = f'Error while creating folder {error}'
            self._logger.error(error_msg)
            return {"error_msg":error_msg}, 500


# TODO somehow merge the following two function
def create_folder_node(query_params) -> object:
    """create folder node using entity_info_service."""

    # if folder is idle then we go on to create the folder
    payload = {**query_params}
    create_url = ConfigClass.ENTITYINFO_SERVICE + 'folders'
    _logger.info('create folder request payload: {}'.format(payload))
    with httpx.Client() as client:
        respon = client.post(create_url, json=payload)
    if respon.status_code != 200:
        error_msg = f'Error while creating folder node : {respon.text}'
        _logger.error(error_msg)
        raise Exception(error_msg)


# if FE passes relative_path
def get_from_db(geid):
    """Get parent folder details from db using global_entity_id."""
    payload = {'global_entity_id': geid}
    node_query_url = ConfigClass.NEO4J_SERVICE + 'nodes/Folder/query'
    with httpx.Client() as client:
        response = client.post(node_query_url, json=payload)
    if response.status_code == 200:
        return response


def validate_folder_name(folder_name):
    regex = re.compile('[/:?.\\*<>|”\']')
    valid = regex.search(folder_name)
    return valid
