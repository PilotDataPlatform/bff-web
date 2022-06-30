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
import json

import requests
from common import LoggerFactory, ProjectClient
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi_utils import cbv

from app.auth import jwt_required
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from services.permissions_service.decorators import PermissionsCheck
from services.permissions_service.utils import get_project_role

_logger = LoggerFactory('api_provenance').get_logger()

router = APIRouter(tags=["Provenance"])


@cbv.cbv(router)
class AuditLog:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/audit-logs/{project_id}',
        summary="Fetch audit logs of a container",
        dependencies=[Depends(PermissionsCheck("audit_logs", "*", "view"))]
    )
    async def get(self, project_id: str, request: Request):
        """
            Fetch audit logs of a container
        """
        _res = APIResponse()
        _logger.info(
            f'Call API for fetching file info for container: {project_id}')

        url = ConfigClass.PROVENANCE_SERVICE + 'audit-logs'

        try:
            page_size = int(request.query_params.get('page_size', 10))
            page = int(request.query_params.get('page', 0))
            order_by = request.query_params.get('order_by', 'createTime')
            order_type = request.query_params.get('order_type', 'desc')

            query = request.query_params.get('query', '{}')
            query = json.loads(query)

            resource = None
            action = None

            params = {
                "page_size": page_size,
                "page": page,
                "order_by": order_by,
                "order_type": order_type,
            }

            if 'start_date' in query:
                params["start_date"] = query["start_date"]

            if 'end_date' in query:
                params["end_date"] = query["end_date"]

            if 'project_code' not in query:
                _logger.error('Missing labels in query')
                _res.set_code(EAPIResponseCode.bad_request)
                _res.set_error_msg(
                    'Missing required parameter project_code')
                return _res.json_response()
            project_code = query['project_code']
            params['project_code'] = project_code

            if 'resource' not in query:
                _logger.error('Missing labels in query')
                _res.set_code(EAPIResponseCode.bad_request)
                _res.set_error_msg('Missing required parameter resource')
                return _res.json_response()
            resource = query['resource']
            params['resource'] = resource

            if 'action' in query:
                action = query['action']
                params['action'] = action

            if self.current_identity['role'] != 'admin':
                project_client = ProjectClient(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
                project = await project_client.get(id=project_id)
                project_role = get_project_role(project.code, self.current_identity)

                if project_role != 'admin':
                    operator = self.current_identity['username']
                    params['operator'] = operator
                else:
                    if 'operator' in query:
                        params['operator'] = query['operator']
            else:
                if 'operator' in query:
                    params['operator'] = query['operator']

            response = requests.get(url, params=params)

            if response.status_code != 200:
                _logger.error(
                    'Failed to query audit log from provenance service:   ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result(
                    'Failed to query audit log from provenance service:   ' + response.text)
                return _res.json_response()
            return response.json()

        except Exception as e:
            raise e
            _logger.error(
                'Failed to query audit log from provenance service:   ' + str(e))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result(
                'Failed to query audit log from provenance service:   ' + str(e))
            return _res.json_response()


@cbv.cbv(router)
class DataLineage:
    current_identity: dict = Depends(jwt_required)

    @router.get(
        '/lineage',
        summary="Lineage",
    )
    async def get(self, request: Request):
        url = ConfigClass.PROVENANCE_SERVICE + "lineage/"
        response = requests.get(url, params=request.query_params)
        return JSONResponse(content=response.json(), status_code=response.status_code)
