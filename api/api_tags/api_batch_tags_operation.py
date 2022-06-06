import requests
from common import LoggerFactory
from flask import request
from flask_jwt import current_identity, jwt_required
from flask_restx import Resource

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
from models.api_response import APIResponse, EAPIResponseCode
from services.meta import get_entities_batch, search_entities

from .utils import check_tag_permissions, get_new_tags

_logger = LoggerFactory('batch_api_tags').get_logger()
api_ns = module_api.namespace(
    'Batch Tags API', description='Batch Tags API', path='/v2')


class APIBatchTagsV2(metaclass=MetaAPI):
    def api_registry(self):
        api_ns.add_resource(self.BatchTagsAPIV2, '/entity/tags')

    class BatchTagsAPIV2(Resource):
        @jwt_required()
        def post(self):
            api_response = APIResponse()
            data = request.get_json()
            only_files = data.get("only_files", False)
            inherit = data.get("inherit", False)
            entity_ids = data.get("entity", [])
            tags = data.get("tags")
            operation = data.get("operation")
            entities = get_entities_batch(entity_ids)
            update_payload = {
                "items": [],
            }
            params = {"ids": []}
            for entity in entities:
                check_tag_permissions(entity, current_identity["username"])

                if inherit:
                    child_entities = search_entities(
                        entity["container_code"],
                        entity["parent_path"] + entity["name"],
                        entity["zone"],
                        recursive=True
                    )
                    for child_entity in child_entities:
                        check_tag_permissions(child_entity, current_identity["username"])

                        if only_files and entity["type"] == "folder":
                            continue

                        update_payload["items"].append({
                            "tags": get_new_tags(operation, child_entity, tags),
                        })
                        params["ids"].append(child_entity["id"])
                if only_files and entity["type"] == "folder":
                    continue

                update_payload["items"].append({
                    "tags": get_new_tags(operation, entity, tags),
                })
                params["ids"].append(entity["id"])

            try:
                response = requests.put(
                    ConfigClass.METADATA_SERVICE + 'items/batch',
                    json=update_payload,
                    params=params
                )
                _logger.info(f"Batch operation result: {response}")
                return response.json(), response.status_code
            except Exception as error:
                _logger.error(f"Error while performing batch operation for tags : {error}")
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result("Error while performing batch operation for tags " + str(error))
                return api_response.to_dict, api_response.code
