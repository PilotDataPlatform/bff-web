import json

import requests
from common import LoggerFactory
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
from models.api_response import APIResponse, EAPIResponseCode
from services.meta import get_entity_by_id
from services.permissions_service.utils import get_project_role

from .utils import check_tag_permissions

_logger = LoggerFactory('api_tags').get_logger()
api_ns = module_api.namespace('Tags API', description='Tags API', path='/v2')


class APITagsV2(metaclass=MetaAPI):
    def api_registry(self):
        api_ns.add_resource(self.TagsAPIV2, '/<entity_id>/tags')

    class TagsAPIV2(Resource):
        @jwt_required()
        def post(self, entity_id):
            api_response = APIResponse()
            data = request.get_json()
            tags = data.get("tags", [])

            if not isinstance(tags, list):
                _logger.error("Tags, project_code are required")
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_error_msg('tags, project_code are required.')
                return api_response.to_dict, api_response.code

            entity = get_entity_by_id(entity_id)
            check_tag_permissions(entity, current_identity["username"])

            project_role = get_project_role(entity["container_code"])

            if not project_role:
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_result("no permission for this project")
                return api_response.to_dict, api_response.code

            try:
                response = requests.put(ConfigClass.METADATA_SERVICE + "item", json=data, params={"id": entity_id})
                _logger.info('Successfully attach tags to entity: {}'.format(json.dumps(response.json())))
                return response.json(), response.status_code
            except Exception as error:
                _logger.error('Failed to attach tags to entity' + str(error))
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_error_msg(str(error))
                return api_response.to_dict, api_response.code
