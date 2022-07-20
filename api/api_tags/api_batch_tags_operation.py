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
from common import LoggerFactory
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from services.meta import get_entities_batch, search_entities

from .utils import check_tag_permissions, get_new_tags

_logger = LoggerFactory('batch_api_tags').get_logger()

router = APIRouter(tags=["Tags"])


@cbv.cbv(router)
class BatchTagsAPIV2:
    current_identity: dict = Depends(jwt_required)

    @router.post(
        '/entity/tags',
        summary="Bulk add or remove tags",
    )
    async def post(self, request: Request):
        api_response = APIResponse()
        data = await request.json()
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
            check_tag_permissions(entity, self.current_identity)

            if inherit:
                if entity["type"] == "folder":
                    child_entities = search_entities(
                        entity["container_code"],
                        entity["parent_path"] + "." + entity["name"],
                        entity["zone"],
                        recursive=True
                    )
                    for child_entity in child_entities:
                        check_tag_permissions(child_entity, self.current_identity)

                        if only_files and child_entity["type"] == "folder":
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

        if not update_payload["items"]:
            api_response.set_result("None updated")
            return api_response.json_response()

        try:
            response = requests.put(
                ConfigClass.METADATA_SERVICE + 'items/batch',
                json=update_payload,
                params=params
            )
            _logger.info(f"Batch operation result: {response}")
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as error:
            _logger.error(f"Error while performing batch operation for tags : {error}")
            api_response.set_code(EAPIResponseCode.internal_error)
            api_response.set_result("Error while performing batch operation for tags " + str(error))
            return api_response.json_response()
