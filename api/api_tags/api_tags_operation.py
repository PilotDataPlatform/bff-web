from flask import request
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from models.api_response import APIResponse, EAPIResponseCode
from services.logger_services.logger_factory_service import SrvLoggerFactory
from config import ConfigClass
from api import module_api
from models.api_meta_class import MetaAPI
import json
import requests

_logger = SrvLoggerFactory('api_tags').get_logger()
api_ns = module_api.namespace('Tags API', description='Tags API', path='/v2')

# rename folder - dont use data_ops_utility
# remove unnecessary comments
# remove taglist validation
# optimize if else
# separate out permission check control


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
                neo4j_response = requests.post(ConfigClass.NEO4J_SERVICE + f'nodes/{entity_type}/query',
                                               json={"global_entity_id": entity_geid})
                if len(neo4j_response.json()) == 0:
                    _logger.info(f"{entity_type} does not exist")
                    _res.set_code(EAPIResponseCode.not_found)
                    _res.set_error_msg(f"{entity_type} does not exist")
                    return _res.to_dict, _res.code

                elif current_identity['role'] == 'admin':
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
                    file_info = neo4j_response.json()[0]
                    uploader = file_info['uploader']
                    file_labels = file_info['labels']
                    root_folder = file_info["display_path"].split("/")[0]
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

                    if len(relations) == 0:
                        _res.set_code(EAPIResponseCode.bad_request)
                        _res.set_result("no permission for this project")
                        return _res.to_dict, _res.code
                    else:
                        relation = relations[0]
                        project_role = relation['r']['type']

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
                            if 'Greenroom' in file_labels and root_folder == current_identity['username']:
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
                            if (root_folder == current_identity['username']) or (ConfigClass.CORE_ZONE_LABEL in file_labels):
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
        node_query_url = ConfigClass.NEO4J_SERVICE + f"/nodes/{entity}/query"
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
