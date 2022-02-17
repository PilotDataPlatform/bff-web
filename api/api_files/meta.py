from flask import request
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from models.api_response import APIResponse, EAPIResponseCode
from services.logger_services.logger_factory_service import SrvLoggerFactory
from services.neo4j_service.neo4j_client import Neo4jClient
from services.permissions_service.utils import has_permission, get_project_role
from config import ConfigClass
import json
import requests
from .utils import parse_json, check_folder_permissions

_logger = SrvLoggerFactory('api_meta').get_logger()


class FileDetailBulk(Resource):
    @jwt_required()
    def post(self):
        api_response = APIResponse()
        response = requests.post(ConfigClass.ENTITYINFO_SERVICE + f"files/bulk/detail", json=request.get_json())
        if response.status_code != 200:
            return response.json(), response.status_code
        file_node = response.json()["result"]

        for file_node in response.json()["result"]:
            if ConfigClass.GREENROOM_ZONE_LABEL in file_node["labels"]:
                zone = "greenroom"
            else:
                zone = "core"
            if not has_permission(file_node["project_code"], "file", zone, "view"):
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_error_msg("Permission Denied")
                return _res.to_dict, _res.code
        return response.json(), response.status_code


class FileDetail(Resource):
    @jwt_required()
    def get(self, file_geid):
        api_response = APIResponse()
        response = requests.get(ConfigClass.ENTITYINFO_SERVICE + f"files/detail/{file_geid}")
        if response.status_code != 200:
            return response.json(), response.status_code
        file_node = response.json()["result"]
        if ConfigClass.GREENROOM_ZONE_LABEL in file_node["labels"]:
            zone = "greenroom"
        else:
            zone = "core"
        neo4j_client = Neo4jClient()
        response = neo4j_client.get_container_by_code(file_node["project_code"])
        if not response.get("result"):
            error_msg = response.get("error_msg", "Neo4j error")
            _logger.error(f'Error fetching project from neo4j: {error_msg}')
            _res.set_code(response.get("code"))
            _res.set_error_msg(error_msg)
            return _res.to_dict, _res.code
        project_node = response.get("result")

        if not has_permission(project_node["code"], "file", zone, "view"):
            _res.set_code(EAPIResponseCode.forbidden)
            _res.set_error_msg("Permission Denied")
            return _res.to_dict, _res.code

        api_response.set_result(file_node)
        return api_response.to_dict, api_response.code


class FileMeta(Resource):
    @jwt_required()
    def get(self, geid):
        """
            Proxy for entity info file META API, handles permission checks
        """
        _res = APIResponse()
        _logger.info(f'Call API for fetching file info: {geid}')
        page_size = int(request.args.get('page_size', 25))
        page = int(request.args.get('page', 0))
        order_by = request.args.get('order_by', 'createTime')
        order_type = request.args.get('order_type', 'desc')
        query = request.args.get('query', '{}')
        partial = request.args.get('partial', '[]')
        zone = request.args.get('zone', '')
        source_type = request.args.get('source_type', '')
        project_geid = request.args.get('project_geid', '')

        required_parameters = ["zone", "project_geid", "source_type"]
        for field in required_parameters:
            if not field in request.args:
                _res.set_code(EAPIResponseCode.bad_request)
                _res.set_error_msg(f'Missing required paramter {field}')
                return _res.to_dict, _res.code

        if zone == "Core":
            zone = ConfigClass.CORE_ZONE_LABEL

        if not zone in [ConfigClass.GREENROOM_ZONE_LABEL, ConfigClass.CORE_ZONE_LABEL, 'All']:
            _logger.error('Invalid zone')
            _res.set_code(EAPIResponseCode.bad_request)
            _res.set_error_msg('Invalid zone')
            return _res.to_dict, _res.code
        if not source_type in ['Project', 'Folder', 'TrashFile', 'Collection']:
            _logger.error('Invalid source_type')
            _res.set_code(EAPIResponseCode.bad_request)
            _res.set_error_msg('Invalid source_type')
            return _res.to_dict, _res.code

        query = parse_json(query)
        partial = parse_json(partial)
        if query is False or partial is False:
            _logger.error(f'Error parsing query json')
            _res.set_code(EAPIResponseCode.bad_request)
            _res.set_error_msg('Invalid json')
            return _res.to_dict, _res.code

        neo4j_client = Neo4jClient()
        response = neo4j_client.get_container_by_geid(project_geid)
        if not response.get("result"):
            if response.get("error_msg") == "Container not found":
                _res.set_code(response.get("code", 500))
                _res.set_error_msg(response.get("error_msg", "Neo4j error"))
            return _res.to_dict, _res.code
        dataset_node = response.get("result")
        project_role = get_project_role(dataset_node["code"])
        
        if project_role in ["contributor", "collaborator"]:
            if not (project_role == "collaborator" and zone == ConfigClass.CORE_ZONE_LABEL):
                if source_type == "Folder":
                    # Listing files in folder
                    response = neo4j_client.node_query("Folder", {"global_entity_id": geid})
                    if not response.get("result"):
                        if response.get("code") == 200:
                            _res.set_code(EAPIResponseCode.not_found)
                            _res.set_error_msg('Folder not found')
                        else:
                            _res.set_code(response.get("code"))
                            _res.set_error_msg(response.get("error_msg", "Neo4j error"))
                        return _res.to_dict, _res.code
                    folder_node = response["result"][0]
                    zone = get_zone(folder_node["labels"])
                    if not check_folder_permissions(folder_node):
                        _res.set_code(EAPIResponseCode.forbidden)
                        _res.set_error_msg("Permission Denied")
                        return _res.to_dict, _res.code
                elif source_type == "TrashFile":
                    query["permissions_display_path"] = current_identity["username"]
                elif source_type  == "Project":
                    # Listing the user folders in project root
                    query["name"] = current_identity["username"]

        if not has_permission(dataset_node["code"], "file", zone.lower(), "view"):
            username = current_identity["username"]
            _logger.info(f"Permissions denied for user {username} in meta listing")
            _res.set_code(EAPIResponseCode.forbidden)
            _res.set_error_msg("Permission Denied")
            return _res.to_dict, _res.code

        try:
            payload = {
                'page': page,
                'page_size': page_size,
                'order_by': order_by,
                'order_type': order_type,
                'zone': zone,
                'source_type': source_type,
                'partial': json.dumps(partial),
                'query': json.dumps(query)
            }

            print(payload)

            url = ConfigClass.ENTITYINFO_SERVICE + f'files/meta/{geid}'
            response = requests.get(url, params=payload)
            _logger.info(f'Calling Entityinfo service, payload is:  ' + str(payload))
            if response.status_code != 200:
                _logger.error('Failed to query data from entityinfo service:  ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result("Failed to query data from entityinfo service")
                return _res.to_dict, _res.code
            else:
                _logger.info('Successfully Fetched file information: {}'.format(json.dumps(response.json())))
                return response.json()
        except Exception as e:
            _logger.error('Failed to query data from entityinfo service:   ' + str(e))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to query data from entityinfo service")
            return _res.to_dict, _res.code
    

class FileMetaHome(Resource):
    @jwt_required()
    def get(self):
        _res = APIResponse()
        _logger.info('Call API for fetching Home folder info')
        page_size = int(request.args.get('page_size', 25))
        page = int(request.args.get('page', 0))
        order_by = request.args.get('order_by', 'createTime')
        order_type = request.args.get('order_type', 'desc')
        query = request.args.get('query', '{}')
        partial = request.args.get('partial', '[]')
        zone = request.args.get('zone', '')
        source_type = request.args.get('source_type', '')
        project_geid = request.args.get('project_geid', '')
        username = current_identity["username"]

        required_parameters = ["zone", "project_geid", "source_type"]
        for field in required_parameters:
            if not field in request.args:
                _res.set_code(EAPIResponseCode.bad_request)
                _res.set_error_msg(f'Missing required paramter {field}')
                return _res.to_dict, _res.code

        query = parse_json(query)
        partial = parse_json(partial)
        if query is False or partial is False:
            _logger.error(f'Error parsing query json')
            _res.set_code(EAPIResponseCode.bad_request)
            _res.set_error_msg('Invalid json')
            return _res.to_dict, _res.code

        if zone == "Core":
            zone = ConfigClass.CORE_ZONE_LABEL

        if not zone in [ConfigClass.GREENROOM_ZONE_LABEL, ConfigClass.CORE_ZONE_LABEL]:
            _logger.error('Invalid zone')
            _res.set_code(EAPIResponseCode.bad_request)
            _res.set_error_msg('Invalid zone')
            return _res.to_dict, _res.code
        if not source_type in ['Folder']:
            _logger.error('Invalid source_type')
            _res.set_code(EAPIResponseCode.bad_request)
            _res.set_error_msg('Invalid source_type')
            return _res.to_dict, _res.code

        neo4j_client = Neo4jClient()
        response = neo4j_client.get_container_by_geid(project_geid)
        if not response.get("result"):
            error_msg = response.get("error_msg", "Neo4j error")
            _logger.error(f'Error fetching dataset from neo4j: {error_msg}')
            _res.set_code(response.get("code"))
            _res.set_error_msg(error_msg)
            return _res.to_dict, _res.code
        dataset_node = response.get("result")

        if not has_permission(dataset_node["code"], "file", zone.lower(), "view"):
            _res.set_code(EAPIResponseCode.forbidden)
            _res.set_error_msg("Permission Denied")
            return _res.to_dict, _res.code

        try:
            payload = {
                "label": "own",
                "start_label": "Container",
                "end_label": zone + ":Folder",
                "start_params": {"id": dataset_node["id"]},
                "end_params": {"name": current_identity["username"]}
            }
            response = requests.post(
                url=ConfigClass.NEO4J_SERVICE + "relations/query",
                json=payload
            )
            if not response.json():
                _logger.info('Home Folder not found')
                _res.set_code(EAPIResponseCode.not_found)
                _res.set_result("Home Folder not found")
                return _res.to_dict, _res.code
            folder_node = response.json()[0]["end_node"]
        except Exception as e:
            _logger.error('Failed to query data from neo4j service:   ' + str(e))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to query data from neo4j service")
            return _res.to_dict, _res.code

        try:
            payload = {
                'page': page,
                'page_size': page_size,
                'order_by': order_by,
                'order_type': order_type,
                'zone': zone,
                'source_type': source_type,
                'partial': json.dumps(partial),
                'query': json.dumps(query)
            }
            folder_geid = folder_node["global_entity_id"]
            url = ConfigClass.ENTITYINFO_SERVICE + f'files/meta/{folder_geid}'
            response = requests.get(url, params=payload)
            _logger.info(f'Calling Entityinfo service, payload is:  ' + str(payload))
            if response.status_code != 200:
                _logger.error('Failed to query data from entityinfo service:  ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result("Failed to query data from entityinfo service")
                return _res.to_dict, _res.code
            else:
                _logger.info('Successfully Fetched file information: {}'.format(json.dumps(response.json())))
                return response.json()
        except Exception as e:
            _logger.error('Failed to query data from entityinfo service:   ' + str(e))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to query data from entityinfo service")
            return _res.to_dict, _res.code


def get_zone(labels: list):
    '''
    Get resource type by neo4j labels
    '''
    zones = [ConfigClass.GREENROOM_ZONE_LABEL, ConfigClass.CORE_ZONE_LABEL]
    for label in labels:
        if label in zones:
            return label
    return None
