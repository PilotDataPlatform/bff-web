from flask import request
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from resources.decorator import check_role
from models.api_response import APIResponse, EAPIResponseCode
from services.logger_services.logger_factory_service import SrvLoggerFactory
from .proxy import BaseProxyResource
from config import ConfigClass
import json
import requests
import time

_logger = SrvLoggerFactory('api_files_ops_v2').get_logger()


class FileTags(Resource):
    @jwt_required()
    def post(self, dataset_id):
        _res = APIResponse()
        _logger.info(f'Call API for attaching tag to file info for container: {dataset_id}')

        try:
            data = request.get_json()
            geid = data.get('geid')
            taglist = data.get('taglist')

            url = ConfigClass.DATA_SERVICE_V2 + 'containers/{}/tags'.format(dataset_id)

            file_url = ConfigClass.NEO4J_SERVICE + 'nodes/File/query'
            file_res = requests.post(file_url, json={"global_entity_id": geid})

            result = file_res.json()

            if len(result) == 0:
                _res.set_code(EAPIResponseCode.bad_request)
                _res.set_error_msg("File is not exist")

                return _res.to_dict, _res.code

            elif current_identity['role'] == 'admin':
                response = requests.post(url, json=data)
                if response.status_code != 200:
                    _logger.error('Failed to attach tags to file:   '+ str(response.text))
                    _res.set_code(EAPIResponseCode.internal_error)
                    _res.set_result("Failed to attach tags to file: " + str(response.text))
                    return _res.to_dict, _res.code
                
                else:
                    # Update Elastic Search Entity
                    es_payload = {
                        "global_entity_id": geid,
                        "updated_fields": {
                            "tags": taglist,
                            "time_lastmodified": time.time()
                        }
                    }
                    es_res = requests.put(ConfigClass.PROVENANCE_SERVICE + 'entity/file', json=es_payload)
                    if es_res.status_code != 200:
                        _res.set_code = EAPIResponseCode.internal_error
                        _res.set_error_msg = f"Elastic Search Error: {es_res.json()}"
                        return _res.to_dict, _res.code
                    _logger.info('Successfully attach tags to file: {}'.format(json.dumps(response.json())))
                    return response.json()

            else:
                file_info = result[0]
                uploader = file_info['uploader']
                file_path = file_info['path']
                file_labels = file_info['labels']

                payload = {
                    "start_label": "User",
                    "end_label": "Container",
                    "start_params": {
                        "name": current_identity['username']
                    },
                    "end_params": {
                        "id": int(dataset_id)
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
                        response = requests.post(url, json=data)
                        if response.status_code != 200:
                            _logger.error('Failed to attach tags to file:   '+ str(response.text))
                            _res.set_code(EAPIResponseCode.internal_error)
                            _res.set_result("Failed to attach tags to file: " + str(response.text))

                            return _res.to_dict, _res.code
                        
                        else:
                            # Update Elastic Search Entity
                            es_payload = {
                                "global_entity_id": geid,
                                "updated_fields": {
                                    "tags": taglist,
                                    "time_lastmodified": time.time()
                                }
                            }
                            es_res = requests.put(ConfigClass.PROVENANCE_SERVICE + 'entity/file', json=es_payload)
                            if es_res.status_code != 200:
                                _res.set_code = EAPIResponseCode.internal_error
                                _res.set_error_msg = f"Elastic Search Error: {es_res.json()}"
                                return _res.to_dict, _res.code

                            _logger.info('Successfully attach tags to file: {}'.format(json.dumps(response.json())))
                            return response.json()
                    
                    elif project_role == 'contributor':
                        if ConfigClass.GREENROOM_ZONE_LABEL in file_labels and uploader == current_identity['username']:
                            response = requests.post(url, json=data)
                            if response.status_code != 200:
                                _logger.error('Failed to attach tags to file:   '+ str(response.text))
                                _res.set_code(EAPIResponseCode.internal_error)
                                _res.set_result("Failed to attach tags to file: " + str(response.text))
                                return _res.to_dict, _res.code
                            
                            else:
                                # Update Elastic Search Entity
                                es_payload = {
                                    "global_entity_id": geid,
                                    "updated_fields": {
                                        "tags": taglist,
                                        "time_lastmodified": time.time()
                                    }
                                }
                                es_res = requests.put(ConfigClass.PROVENANCE_SERVICE + 'entity/file', json=es_payload)
                                if es_res.status_code != 200:
                                    _res.set_code = EAPIResponseCode.internal_error
                                    _res.set_error_msg = f"Elastic Search Error: {es_res.json()}"
                                    return _res.to_dict, _res.code

                                _logger.info('Successfully attach tags to file: {}'.format(json.dumps(response.json())))
                                return response.json()
                        else:
                            _logger.error('Failed to attach tags to file:  contributors can only attach their own greenroom raw file')
                            _res.set_code(EAPIResponseCode.forbidden)
                            _res.set_result("Failed to attach tags to file:  contributors can only attach their own greenroom raw file")
                            return _res.to_dict, _res.code

                    elif project_role == 'collaborator':
                        if (uploader == current_identity['username']) or (ConfigClass.CORE_ZONE_LABEL in file_labels):
                            response = requests.post(url, json=data)
                            if response.status_code != 200:
                                _logger.error('Failed to attach tags to file:   '+ str(response.text))
                                _res.set_code(EAPIResponseCode.internal_error)
                                _res.set_result("Failed to attach tags to file: " + str(response.text))
                                return _res.to_dict, _res.code
                            
                            else:
                                # Update Elastic Search Entity
                                es_payload = {
                                    "global_entity_id": geid,
                                    "updated_fields": {
                                        "tags": taglist,
                                        "time_lastmodified": time.time()
                                    }
                                }
                                es_res = requests.put(ConfigClass.PROVENANCE_SERVICE + 'entity/file', json=es_payload)
                                if es_res.status_code != 200:
                                    _res.set_code = EAPIResponseCode.internal_error
                                    _res.set_error_msg = f"Elastic Search Error: {es_res.json()}"
                                    return _res.to_dict, _res.code
                                _logger.info('Successfully attach tags to file: {}'.format(json.dumps(response.json())))
                                return response.json()
                        else:
                            _logger.error('Failed to attach tags to file:  collaborator can only attach their own raw file')
                            _res.set_code(EAPIResponseCode.forbidden)
                            _res.set_result("Failed to attach tags to file:  collaborator can only attach their own raw file")
                            return _res.to_dict, _res.code

        except Exception as e:
            _logger.error(
                'Failed to convert query into json.' + str(e))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_error_msg(str(e))

            return _res.to_dict, _res.code

    @jwt_required()
    def delete(self, dataset_id):
        _res = APIResponse()
        _logger.info(f'Call API for deleting tag to file info for container: {dataset_id}')

        try:
            data = request.get_json()
            geid = data.get('geid')
            taglist = data.get('taglist')

            url = ConfigClass.DATA_SERVICE_V2 + 'containers/{}/tags'.format(dataset_id)

            file_url = ConfigClass.NEO4J_SERVICE + 'nodes/File/query'
            file_res = requests.post(file_url, json={"global_entity_id": geid})

            result = file_res.json()

            if len(result) == 0:
                _res.set_code(EAPIResponseCode.bad_request)
                _res.set_error_msg("File is not exist")

                return _res.to_dict, _res.code

            elif current_identity['role'] == 'admin':
                response = requests.delete(url, json=data)
                if response.status_code != 200:
                    _logger.error('Failed to delete tags from file:   '+ str(response.text))
                    _res.set_code(EAPIResponseCode.internal_error)
                    _res.set_result("Failed to delete tags from file: " + str(response.text))
                    return _res.to_dict, _res.code
                
                else:
                    # Update Elastic Search Entity
                    es_payload = {
                        "global_entity_id": geid,
                        "updated_fields": {
                            "tags": taglist,
                            "time_lastmodified": time.time()
                        }
                    }
                    es_res = requests.put(ConfigClass.PROVENANCE_SERVICE + 'entity/file', json=es_payload)
                    if es_res.status_code != 200:
                        _res.set_code = EAPIResponseCode.internal_error
                        _res.set_error_msg = f"Elastic Search Error: {es_res.json()}"
                        return _res.to_dict, _res.code
                    _logger.info('Successfully delete tags from file: {}'.format(json.dumps(response.json())))
                    return response.json()

            else:
                file_info = result[0]
                uploader = file_info['uploader']
                file_path = file_info['path']
                file_labels = file_info['labels']

                payload = {
                    "start_label": "User",
                    "end_label": "Container",
                    "start_params": {
                        "name": current_identity['username']
                    },
                    "end_params": {
                        "id": int(dataset_id)
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
                        response = requests.delete(url, json=data)
                        if response.status_code != 200:
                            _logger.error('Failed to delete tags from file:   '+ str(response.text))
                            _res.set_code(EAPIResponseCode.internal_error)
                            _res.set_result("Failed to delete tags from file: " + str(response.text))
                            return _res.to_dict, _res.code
                        
                        else:
                            # Update Elastic Search Entity
                            es_payload = {
                                "global_entity_id": geid,
                                "updated_fields": {
                                    "tags": taglist,
                                    "time_lastmodified": time.time()
                                }
                            }
                            es_res = requests.put(ConfigClass.PROVENANCE_SERVICE + 'entity/file', json=es_payload)
                            if es_res.status_code != 200:
                                _res.set_code = EAPIResponseCode.internal_error
                                _res.set_error_msg = f"Elastic Search Error: {es_res.json()}"
                                return _res.to_dict, _res.code
                            _logger.info('Successfully attach tags to file: {}'.format(json.dumps(response.json())))
                            return response.json()
                    
                    elif project_role == 'contributor':
                        if ConfigClass.GREENROOM_ZONE_LABEL in file_labels and uploader == current_identity['username']:
                            response = requests.delete(url, json=data)
                            if response.status_code != 200:
                                _logger.error('Failed to delete tags from file:   '+ str(response.text))
                                _res.set_code(EAPIResponseCode.internal_error)
                                _res.set_result("Failed to delete tags from file: " + str(response.text))
                                return _res.to_dict, _res.code
                            
                            else:
                                # Update Elastic Search Entity
                                es_payload = {
                                    "global_entity_id": geid,
                                    "updated_fields": {
                                        "tags": taglist,
                                        "time_lastmodified": time.time()
                                    }
                                }
                                es_res = requests.put(ConfigClass.PROVENANCE_SERVICE + 'entity/file', json=es_payload)
                                if es_res.status_code != 200:
                                    _res.set_code = EAPIResponseCode.internal_error
                                    _res.set_error_msg = f"Elastic Search Error: {es_res.json()}"
                                    return _res.to_dict, _res.code

                                _logger.info('Successfully delete tags from file: {}'.format(json.dumps(response.json())))
                                return response.json()
                        else:
                            _logger.error('Failed to delete tags from file:  contributors can only delete their own greenroom raw file')
                            _res.set_code(EAPIResponseCode.forbidden)
                            _res.set_result("Failed to delete tags from file:  contributors can only delete their own greenroom raw file")
                            return _res.to_dict, _res.code

                    elif project_role == 'collaborator':
                        if (uploader == current_identity['username']) or (ConfigClass.CORE_ZONE_LABEL in file_labels in file_labels):
                            response = requests.delete(url, json=data)
                            if response.status_code != 200:
                                _logger.error('Failed to delete tags from file:   '+ str(response.text))
                                _res.set_code(EAPIResponseCode.internal_error)
                                _res.set_result("Failed to delete tags from file: " + str(response.text))
                                return _res.to_dict, _res.code
                            
                            else:
                                # Update Elastic Search Entity
                                es_payload = {
                                    "global_entity_id": geid,
                                    "updated_fields": {
                                        "tags": taglist,
                                        "time_lastmodified": time.time()
                                    }
                                }
                                es_res = requests.put(ConfigClass.PROVENANCE_SERVICE + 'entity/file', json=es_payload)
                                if es_res.status_code != 200:
                                    _res.set_code = EAPIResponseCode.internal_error
                                    _res.set_error_msg = f"Elastic Search Error: {es_res.json()}"
                                    return _res.to_dict, _res.code
                                _logger.info('Successfully delete tags to file: {}'.format(json.dumps(response.json())))
                                return response.json()
                        else:
                            _logger.error('Failed to delete tags from file:  collaborator can only delete their own raw file')
                            _res.set_code(EAPIResponseCode.forbidden)
                            _res.set_result("Failed to delete tags from file:  collaborator can only delete their own raw file")
                            return _res.to_dict, _res.code

        except Exception as e:
            _logger.error(
                'Failed to convert query into json.' + str(e))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_error_msg(str(e))

            return _res.to_dict, _res.code
