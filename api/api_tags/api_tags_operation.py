from flask import request
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from models.api_response import APIResponse, EAPIResponseCode
from common import LoggerFactory
from config import ConfigClass
from api import module_api
from models.api_meta_class import MetaAPI
import json
import requests
from services.permissions_service.utils import get_project_role
from services.meta import get_entity_by_id

_logger = LoggerFactory('api_tags').get_logger()
api_ns = module_api.namespace('Tags API', description='Tags API', path='/v2')


class APITagsV2(metaclass=MetaAPI):
    def api_registry(self):
        api_ns.add_resource(self.TagsAPIV2, '/<entity_type>/<entity_geid>/tags')

    class TagsAPIV2(Resource):
        @jwt_required()
        # @check_role('uploader')
        def post(self, entity_type, entity_geid):
            _res = APIResponse()
            data = request.get_json()
            taglist = data.get("tags", [])
            project_code = http_query_project_code(geid=entity_geid, entity=entity_type)
            tags_url = ConfigClass.DATA_UTILITY_SERVICE_v2 + f'{entity_type}/{entity_geid}/tags'
            if not isinstance(taglist, list) or not project_code:
                _logger.error("Tags, project_code are required")
                _res.set_code(EAPIResponseCode.bad_request)
                _res.set_error_msg('tags, project_code are required.')
                return _res.to_dict, _res.code
            try:
                file_info = get_entity_by_id(entity_geid)
                if current_identity['role'] == 'admin':
                    response = requests.post(tags_url, json=data)
                    if response.status_code != 200:
                        _logger.error('Failed to attach tags to entity:   ' + str(response.text))
                        _res.set_code(EAPIResponseCode.internal_error)
                        _res.set_result("Failed to attach tags to entity: " + str(response.text))
                        return _res.to_dict, _res.code
                    _logger.info(
                        'Successfully attach tags to entity: {}'.format(json.dumps(response.json())))
                    return response.json()

                else:
                    uploader = file_info['owner']
                    zone = "greenroom" if file_info["zone"] == 1 else "core"
                    root_folder = file_info["parent_path"].split(".")[0]
                    project_role = get_project_role(project_code)

                    if not project_role:
                        _res.set_code(EAPIResponseCode.bad_request)
                        _res.set_result("no permission for this project")
                        return _res.to_dict, _res.code

                    if project_role == 'admin':
                        response = requests.post(tags_url, json=data)
                        if response.status_code != 200:
                            _logger.error('Failed to attach tags to entity:   ' + str(response.text))
                            _res.set_code(EAPIResponseCode.internal_error)
                            _res.set_result("Failed to attach tags to entity: " + str(response.text))

                            return _res.to_dict, _res.code
                        _logger.info(
                            'Successfully attach tags to entity: {}'.format(json.dumps(response.json())))
                        return response.json()

                    elif project_role == 'contributor':
                        if zone == "greenroom" and root_folder == current_identity['username']:
                            response = requests.post(tags_url, json=data)
                            if response.status_code != 200:
                                _logger.error('Failed to attach tags to entity:   ' + str(response.text))
                                _res.set_code(EAPIResponseCode.internal_error)
                                _res.set_result("Failed to attach tags to entity: " + str(response.text))
                                return _res.to_dict, _res.code
                            _logger.info(
                                'Successfully attach tags to entity: {}'.format(json.dumps(response.json())))
                            return response.json()
                        else:
                            _logger.error(
                                'Failed to attach tags to entity:  contributors can only attach their own greenroom raw file')
                            _res.set_code(EAPIResponseCode.forbidden)
                            _res.set_result(
                                'Failed to attach tags to entity:  contributors can only attach their own greenroom raw file')
                            return _res.to_dict, _res.code

                    elif project_role == 'collaborator':
                        if root_folder == current_identity['username'] or zone == "core":
                            response = requests.post(tags_url, json=data)
                            if response.status_code != 200:
                                _logger.error('Failed to attach tags to entity:   ' + str(response.text))
                                _res.set_code(EAPIResponseCode.internal_error)
                                _res.set_result("Failed to attach tags to entity: " + str(response.text))
                                return _res.to_dict, _res.code
                            _logger.info(
                                'Successfully attach tags to entity: {}'.format(json.dumps(response.json())))
                            return response.json()
                        else:
                            _logger.error('Failed to attach tags to entity:  collaborator can only attach their own raw file')
                            _res.set_code(EAPIResponseCode.forbidden)
                            _res.set_result(
                                "Failed to attach tags to entity:  collaborator can only attach their own raw file")
                            return _res.to_dict, _res.code
            except Exception as error:
                _logger.error(
                    'Failed to attach tags to entity' + str(error))
                _res.set_code( EAPIResponseCode.internal_error)
                _res.set_error_msg(str(error))
                return _res.to_dict, _res.code


def http_query_project_code(geid, entity):
    _res = APIResponse()
    try:

        payload = {
            "global_entity_id": geid
        }
        node_query_url = ConfigClass.NEO4J_SERVICE + f"nodes/{entity}/query"
        response = requests.post(node_query_url, json=payload)
        if response.status_code != 200:
            _logger.error('Failed to query project from neo4j service:   ' + response.text)
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to query project from neo4j service")
            return _res.to_dict, _res.code
        else:
            response = response.json()
            project_code = response[0]["project_code"]
            return project_code
    except Exception as e:
        _logger.error('Failed to query project from neo4j service:   ' + str(e))
        _res.set_code(EAPIResponseCode.internal_error)
        _res.set_result("Failed to query project from neo4j service")
        return _res.to_dict, _res.code
