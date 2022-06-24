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
from flask import request
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from models.api_response import APIResponse, EAPIResponseCode
from common import LoggerFactory, ProjectClientSync
from services.permissions_service.utils import get_project_role, get_project_code_from_request
from config import ConfigClass
import json
import requests

_logger = LoggerFactory('api_files_ops_v4').get_logger()


class FileSearch(Resource):
    @jwt_required()
    def get(self, project_geid):
        """
            Fetch file info from Elastic Search
        """
        _res = APIResponse()

        page_size = int(request.args.get('page_size', 10))
        page = int(request.args.get('page', 0))
        order_by = request.args.get('order_by', 'time_created')
        order_type = request.args.get('order_type', 'desc')
        query = request.args.get('query', '{}')

        project_code = None

        query = json.loads(query)
        query_params = {"global_entity_id": project_geid}
        if current_identity['role'] != 'admin':
            project_code = get_project_code_from_request({"project_geid": project_geid})
            project_role = get_project_role(project_code)
            if project_role == 'contributor':
                # Make sure contributor is restrict to querying there own files/folders
                # the reason use display_path is all own files/folders under user's name folder
                if 'display_path' not in query:
                    _logger.error(
                        'Non-admin user does not have access to query all user file info')
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_error_msg(
                        'Permission Deined, Non-admin user does not have access to query all user file info')
                    return _res.json_response()
                elif current_identity['username'] not in query['display_path']['value']:
                    _logger.error(
                        'Non-admin user can noly have access to their own file info')
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_error_msg(
                        'Permission Deined, Non-admin user can noly have access to their own file info')
                    return _res.json_response()
                elif 'zone' not in query:
                    _logger.error(
                        'zone and file_type is required if user role is contributor')
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_error_msg(
                        'Permission Deined, zone and file_type is required if user role is contributor')
                    return _res.json_response()
                elif query['zone']['value'] == 'core':
                    _logger.error(
                        'contributor cannot fetch core files or processed files')
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_error_msg(
                        'Permission Deined, contributor cannot fetch core files or processed files')
                    return _res.json_response()

            elif project_role == 'collaborator':
                if query['zone']['value'] == 'greenroom' and 'display_path' not in query:
                    _logger.error(
                        'collaborator user does not have access to query all greenroom file info')
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_error_msg('Permission Deined')
                    return _res.json_response()
                elif 'display_path' in query and current_identity['username'] not in query['display_path']['value']:
                    _logger.error(
                        'collaborator user can noly have access to their own file info')
                    _res.set_code(EAPIResponseCode.forbidden)
                    _res.set_error_msg('Permission Deined')
                    return _res.json_response()


        project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
        project = project_client.get(id=project_geid)
        project_code = project.code

        try:
            query["project_code"] = {
                "value": project_code,
                "condition": "equal"
            }
            query = json.dumps(query)
            params = {
                "page": page,
                "page_size": page_size,
                "sort_type": order_type,
                "sort_by": order_by,
                "query": query
            }

            url = ConfigClass.PROVENANCE_SERVICE + 'entity/file'
            response = requests.get(url, params=params)
            _logger.info(
                f'Calling Provenance service /v1/entity/file, payload is:  ' + str(params))
            if response.status_code != 200:
                _logger.error(
                    'Failed to query data from Provenance service:   ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result("Failed to query data from Provenance service")
                return _res.json_response()
            else:
                _logger.info('Successfully Fetched file information')
                return response.json()

        except Exception as e:
            _logger.error('Failed to query data from es service:   ' + str(e))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to query data from es service")
            return _res.json_response()
