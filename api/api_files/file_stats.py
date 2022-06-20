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
from common import LoggerFactory
from services.permissions_service.decorators import permissions_check, get_project_code_from_request
from services.permissions_service.utils import get_project_role
from config import ConfigClass
import json
import requests

_logger = LoggerFactory('api_file_statistics').get_logger()


class FileStatistics(Resource):
    @jwt_required()
    @permissions_check('file_stats', '*', 'view')
    def get(self, project_geid):
        """
            Return file statistics to the frontend, proxy entity info service, add permission control
        """
        _res = APIResponse()
        try:
            url = ConfigClass.ENTITYINFO_SERVICE + "project/{}/files/statistics".format(project_geid)
            current_role = current_identity['role']
            user_id = current_identity["user_id"]
            operator = current_identity['username']
            start_date = request.args['start_date']
            end_date = request.args['end_date']
            query_params = {
                "start_date": start_date,
                "end_date": end_date
            }
            project_code = get_project_code_from_request({"project_geid": project_geid})
            project_role = get_project_role(project_code)

            # Permission control
            # Upload & Download (user based statistics)Project admin could get a total file number for all files
            # Platform admin and project admin has full access
            if current_role == 'admin' or project_role == 'admin':
                fetched_stats = requests.get(url, params=query_params)
                if not fetched_stats.status_code == 200:
                    raise("Error when fetching stats, payload: " + str(query_params))
                _res.set_code(EAPIResponseCode.success)
                result = fetched_stats.json()['result']
                result['current_role'] = current_role
                result['operator'] = operator
                result['query_params'] = query_params
                result['policy'] = "fa"
                _res.set_result(result)
                return _res.to_dict, _res.code
            # Not Admin
            # Project collabrator/contributor could get a total file number of their own files in greenroom
            # Project contributor cannot get any information in core but collabrator and admin could get the total number of files in core
            query_params['operator'] = operator
            fetched_stats = requests.get(url, params=query_params)
            if not fetched_stats.status_code == 200:
                raise("Error when fetching stats, payload: " + str(query_params))
            _res.set_code(EAPIResponseCode.success)
            result = fetched_stats.json()['result']
            if project_role == "contributor":
                # deactivate core stats
                result['core'] = None
                result['approved'] = None
            # project collabrator can see all files in core
            if project_role == "collaborator":
                query_params['operator'] = None
                all_fetched_stats = requests.get(url, params=query_params)
                if not all_fetched_stats.status_code == 200:
                    raise("Error when fetching stats, payload: " + str(query_params))
                result['core'] = all_fetched_stats.json()['result']['core']
            result['current_role'] = current_role
            result['operator'] = operator
            result['query_params'] = query_params
            _res.set_code(EAPIResponseCode.success)
            _res.set_result(result)
            return _res.to_dict, _res.code
        except Exception as e:
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_error_msg(str(e))
            return _res.to_dict, _res.code
