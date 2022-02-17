from flask import request
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from models.api_response import APIResponse, EAPIResponseCode
from services.logger_services.logger_factory_service import SrvLoggerFactory
from config import ConfigClass
import json
from models.api_meta_class import MetaAPI
import requests
from api import module_api
from resources.validations import boolean_validate_role

_logger = SrvLoggerFactory('api_folder_creation_v1').get_logger()

api_ns = module_api.namespace('FolderCreation', description='FolderCreation API', path='/v1')


class APIFolderCreation(metaclass=MetaAPI):
    def api_registry(self):
        api_ns.add_resource(self.FolderCreation, '/folder')

    class FolderCreation(Resource):
        @jwt_required()
        def post(self):
            _res = APIResponse()
            req_data = request.get_json()
            uploader = req_data.get('uploader')
            project_code = req_data.get('project_code')
            zone = req_data.get('zone')
            destination_geid = req_data.get('destination_geid', None)
            try:
                project_data = get_project_geid(project_code=project_code)
                if len(project_data.json()) < 1:
                    _logger.error('There is no project in neo4j service:   ' + project_data.text)
                    _res.set_code(EAPIResponseCode.internal_error)
                    _res.set_result("There is no project in neo4j servic, which id is ".format(project_code))
                    return _res.to_dict, _res.code
                if current_identity['role'] != 'admin':
                    project_role = get_project_role(project_code=project_code)
                    if not project_role:
                        _res.set_code(EAPIResponseCode.bad_request)
                        _res.set_result("no permission for this project")
                        return _res.to_dict, _res.code
                    if project_role == 'contributor':
                        # contributor is restricted to creating folder only in greenroom
                        if zone == 'core':
                            _logger.error('Permission Deined, Contributor cannot create folder in core')
                            _res.set_code(EAPIResponseCode.forbidden)
                            _res.set_error_msg(
                                'Permission Deined, Contributor cannot create folder in core')
                            return _res.to_dict, _res.code
                        elif uploader != current_identity['username']:
                            _res.set_code(EAPIResponseCode.forbidden)
                            _res.set_error_msg(
                                "Permission Deined,Non-admin user can only have access to create under their own " \
                                "folder")
                            _logger.error('Permission Deined,Non-admin user can only have access to create under their own " \
                                             "folder')
                            return _res.to_dict, _res.code
                    elif project_role == 'collaborator':
                        # collaborator can only create sub folder under his own folder if zone is greenroom
                        # if zone is core, collaborator can create folder anywhere
                        if zone == 'greenroom':
                            if destination_geid is not None:
                                # check if parent folder uploader is same as current uploader
                                destination_folder_uploader = get_destination_folder_uploader(destination_geid)
                                if destination_folder_uploader != uploader:
                                    _res.set_code(EAPIResponseCode.forbidden)
                                    _res.set_error_msg(
                                        "Permission Deined,Non-admin user can only have access to create under their "
                                        "own folder in greenroom")
                                    _logger.error('Permission Deined,Non-admin user can only have access to create under their own " \
                                                                                     "folder in greenroom')
                                    return _res.to_dict, _res.code
                # neo4j to check if project exists

                # create folder - call service upload
                try:
                    folder_name = req_data.get('folder_name')
                    tags = req_data.get('tags')
                    destination_geid = req_data.get('destination_geid')
                    if destination_geid is not None:
                        destination_geid = req_data.get('destination_geid')
                    payload = {
                        "folder_name": folder_name,
                        "destination_geid": destination_geid,
                        "project_code": project_code,
                        "uploader": uploader,
                        "tags": tags,
                        "zone": zone
                    }
                    folder_creation_url = None
                    if zone == 'core':
                        folder_creation_url = ConfigClass.DATA_UPLOAD_SERVICE_CORE + '/folder'
                    elif zone == 'greenroom':
                        folder_creation_url = ConfigClass.DATA_UPLOAD_SERVICE_GREENROOM + '/folder'
                    response = requests.post(folder_creation_url, data=json.dumps(payload))
                    print(folder_creation_url)
                    return response.json(), response.status_code
                except Exception as error:
                    _logger.error("Error while creating folder")
                    _res.set_code(EAPIResponseCode.internal_error)
                    _res.set_result("Failed to create folder")
                    return _res.to_dict, _res.code

            except Exception as error:
                _logger.error("Error while creating folder")
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result("Failed to create folder")
                return _res.to_dict, _res.code


def get_project_role(project_code):
    _res = APIResponse()
    payload = {
        "start_label": "User",
        "end_label": "Container",
        "start_params": {
            "name": current_identity['username']
        },
        "end_params": {
            "code": project_code
        }
    }
    relation_res = requests.post(ConfigClass.NEO4J_SERVICE + 'relations/query', json=payload)
    relations = relation_res.json()

    if len(relations) != 0:
        relation = relations[0]
        project_role = relation['r']['type']
        return project_role
    else:
        return False


def get_project_geid(project_code):
    _res = APIResponse()
    try:

        payload = {
            "code": project_code
        }
        node_query_url = ConfigClass.NEO4J_SERVICE + "nodes/Container/query"
        response = requests.post(node_query_url, json=payload)
        if response.status_code != 200:
            _logger.error('Failed to query project from neo4j service:   ' + response.text)
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to query project from neo4j service")
            return _res.to_dict, _res.code
        else:
            return response
    except Exception as e:
        _logger.error('Failed to query project from neo4j service:   ' + str(e))
        _res.set_code(EAPIResponseCode.internal_error)
        _res.set_result("Failed to query project from neo4j service")
        return _res.to_dict, _res.code


def get_destination_folder_uploader(destination_geid):
    _res = APIResponse()
    payload = {
        "global_entity_id": destination_geid
    }
    node_query_url = ConfigClass.NEO4J_SERVICE + "nodes/Folder/query"
    response = requests.post(node_query_url, json=payload)

    if response.status_code != 200:
        _logger.error('Failed to query project from neo4j service:   ' + response.text)
        _res.set_code(EAPIResponseCode.internal_error)
        _res.set_result("Failed to query project from neo4j service")
        return _res.to_dict, _res.code
    else:
        destination_folder_uploader = response.json()[0]["uploader"]
        return destination_folder_uploader

