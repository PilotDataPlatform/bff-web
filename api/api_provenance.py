from flask import request
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from .api_files.proxy import BaseProxyResource
from models.api_response import APIResponse, EAPIResponseCode
from services.logger_services.logger_factory_service import SrvLoggerFactory
from models.api_meta_class import MetaAPI
from config import ConfigClass
from resources.utils import get_container_id
import json
import requests
from api import module_api
from services.permissions_service.decorators import permissions_check

_logger = SrvLoggerFactory('api_provenance').get_logger()

api_provenance = module_api.namespace(
    'Provenance', description='Provenance API', path='/v1')


class APIProvenance(metaclass=MetaAPI):
    def api_registry(self):
        # api_provenance.add_resource(self.AuditLog, '/audit-logs/<dataset_id>')
        api_provenance.add_resource(
            self.AuditLog, '/audit-logs/<project_geid>')
        api_provenance.add_resource(self.DataLineage, '/lineage')

    class AuditLog(Resource):
        @jwt_required()
        @permissions_check('audit_logs', '*', 'view')
        def get(self, project_geid):
            """
                Fetch audit logs of a container
            """
            _res = APIResponse()
            _logger.info(
                f'Call API for fetching file info for container: {project_geid}')

            url = ConfigClass.PROVENANCE_SERVICE + 'audit-logs'

            try:
                page_size = int(request.args.get('page_size', 10))
                page = int(request.args.get('page', 0))
                order_by = request.args.get('order_by', 'createTime')
                order_type = request.args.get('order_type', 'desc')

                query = request.args.get('query', '{}')
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
                    return _res.to_dict, _res.code
                else:
                    project_code = query['project_code']
                    params['project_code'] = project_code

                if 'resource' not in query:
                    _logger.error('Missing labels in query')
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_error_msg('Missing required parameter resource')
                    return _res.to_dict, _res.code
                else:
                    resource = query['resource']
                    params['resource'] = resource

                if 'action' in query:
                    action = query['action']
                    params['action'] = action

                if current_identity['role'] != 'admin':
                    query_params = {"global_entity_id": project_geid}
                    container_id = get_container_id(query_params)
                    payload = {
                        "start_label": "User",
                        "end_label": "Container",
                        "start_params": {
                            "name": current_identity['username']
                        },
                        "end_params": {
                            "id": int(container_id)
                        }
                    }

                    relation_res = requests.post(
                        ConfigClass.NEO4J_SERVICE + 'relations/query', json=payload)
                    relations = relation_res.json()

                    if len(relations) == 0:
                        _res.set_code(EAPIResponseCode.bad_request)
                        _res.set_result("no permission for this project")
                        return _res.to_dict, _res.code

                    relation = relations[0]
                    project_role = relation['r']['type']

                    if project_role != 'admin':
                        operator = current_identity['username']
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
                    return _res.to_dict, _res.code
                else:
                    return response.json()

            except Exception as e:
                _logger.error(
                    'Failed to query audit log from provenance service:   ' + str(e))
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result(
                    'Failed to query audit log from provenance service:   ' + str(e))
                return _res.to_dict, _res.code

    class DataLineage(BaseProxyResource):
        url = ConfigClass.PROVENANCE_SERVICE + "lineage/"
        methods = ["GET"]
        required_roles = {"GET": "member"}
