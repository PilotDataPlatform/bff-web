import requests
from common import LoggerFactory
from flask import request
from flask_jwt import current_identity
from flask_jwt import jwt_required
from flask_restx import Resource

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
from models.api_response import APIResponse
from models.api_response import EAPIResponseCode
from resources.error_handler import APIException
from resources.swagger_modules import data_manifests
from resources.swagger_modules import data_manifests_return
from services.meta import get_entity_by_id
from services.permissions_service.decorators import permissions_check
from services.permissions_service.utils import get_project_role
from services.permissions_service.utils import has_permission

from .utils import has_permissions

api_ns_data_manifests = module_api.namespace(
    'Attribute Templates Restful', description='For data attribute templates feature', path='/v1')
api_ns_data_manifest = module_api.namespace(
    'Attribute Templates Restful', description='For data attribute templates feature', path='/v1')

_logger = LoggerFactory('api_data_manifest').get_logger()


class APIDataManifest(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_data_manifests.add_resource(
            self.RestfulManifests, '/data/manifests')
        api_ns_data_manifest.add_resource(
            self.RestfulManifest, '/data/manifest/<manifest_id>')
        api_ns_data_manifest.add_resource(self.FileAttributes, '/file/<file_geid>/manifest')
        api_ns_data_manifest.add_resource(
            self.ImportManifest, '/import/manifest')
        api_ns_data_manifest.add_resource(
            self.FileManifestQuery, '/file/manifest/query')
        api_ns_data_manifest.add_resource(
            self.AttachAttributes, '/file/attributes/attach')

    class RestfulManifests(Resource):
        @api_ns_data_manifest.expect(data_manifests)
        @api_ns_data_manifest.response(200, data_manifests_return)
        @jwt_required()
        @permissions_check('file_attribute_template', '*', 'view')
        def get(self):
            """List attribute templates by project_code."""
            try:
                response = requests.get(
                    ConfigClass.METADATA_SERVICE + 'template/', params=request.args)
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f'Error when calling metadata service: {str(e)}')
                error_msg = {
                    'result': str(e)
                }
                return error_msg, 500

        @jwt_required()
        @permissions_check('file_attribute_template', '*', 'create')
        def post(self):
            """Create a new attribute template."""
            try:
                response = requests.post(
                    ConfigClass.METADATA_SERVICE + 'template/', json=request.get_json())
                return response.json(), response.status_code
            except Exception as e:
                _logger.error(
                    f'Error when calling metadata service: {str(e)}')
                error_msg = {
                    'result': str(e)
                }
                return error_msg, 500

    class RestfulManifest(Resource):
        @jwt_required()
        def get(self, manifest_id):
            """Get an attribute template by id."""
            my_res = APIResponse()
            try:
                response = requests.get(
                    ConfigClass.METADATA_SERVICE + f'template/{manifest_id}/')
                res = response.json()
                if not res['result']:
                    my_res.set_code(EAPIResponseCode.not_found)
                    my_res.set_error_msg('Attribute template not found')
                    return my_res.to_dict, my_res.code

                for attr in res['result']['attributes']:
                    attr['manifest_id'] = res['result']['id']
                return res, response.status_code
            except Exception as e:
                _logger.error(
                    f'Error when calling metadata service: {str(e)}')
                error_msg = {
                    'result': str(e)
                }
                return error_msg, 500

        @jwt_required()
        def put(self, manifest_id):
            """Update attributes or name of template by id."""
            my_res = APIResponse()
            data = request.get_json()
            project_code = data.get('project_code')
            # Permissions check
            if not has_permission(project_code, 'file_attribute_template', '*', 'update'):
                my_res.set_code(EAPIResponseCode.forbidden)
                my_res.set_result('Permission Denied')
                return my_res.to_dict, my_res.code

            try:
                response = requests.get(
                    ConfigClass.METADATA_SERVICE + f'template/{manifest_id}/')
                template = response.json()['result']
                if not template:
                    my_res.set_code(EAPIResponseCode.not_found)
                    my_res.set_error_msg('Attribute template not found')
                    return my_res.to_dict, my_res.code

                if 'attributes' not in data:
                    result = {'id': template['id'], 'name': template['name'], 'project_code': template['project_code']}
                    data['attributes'] = template['attributes']
                else:
                    result = ''
                    existing_attr = template['attributes']
                    data['attributes'] = data['attributes'] + existing_attr

                params = {'id': manifest_id}
                response = requests.put(
                    ConfigClass.METADATA_SERVICE + 'template/', params=params, json=data)
                res = response.json()
                res['result'] = result
                return res, response.status_code
            except Exception as e:
                _logger.error(
                    f'Error when calling metadata service: {str(e)}')
                error_msg = {
                    'result': str(e)
                }
                return error_msg, 500

        @jwt_required()
        def delete(self, manifest_id):
            """Delete an attribute template."""
            my_res = APIResponse()
            response = requests.get(
                ConfigClass.METADATA_SERVICE + f'template/{manifest_id}/')
            res = response.json()['result']
            if not res:
                my_res.set_code(EAPIResponseCode.not_found)
                my_res.set_error_msg('Attribute template not found')
                return my_res.to_dict, my_res.code

            project_code = res['project_code']
            # Permissions check
            if not has_permission(project_code, 'file_attribute_template', '*', 'delete'):
                my_res.set_code(EAPIResponseCode.forbidden)
                my_res.set_result('Permission Denied')
                return my_res.to_dict, my_res.code

            try:
                # check if template attached to items
                for zone in [0, 1]:
                    for archived in [True, False]:
                        params = {'container_code': project_code, 'zone': zone, 'recursive': True, 'archived': archived,
                                  'type': 'file'}
                        response = requests.get(ConfigClass.METADATA_SERVICE + 'items/search/', params=params)
                        if response.status_code != 200:
                            my_res.set_code(EAPIResponseCode.internal_error)
                            my_res.set_error_msg('Failed to search for items')
                            return my_res.to_dict, my_res.code
                        else:
                            items = response.json()['result']
                            for item in items:
                                if manifest_id in item['extended']['extra']['attributes']:
                                    my_res.set_code(EAPIResponseCode.forbidden)
                                    my_res.set_result('Cant delete manifest attached to files')
                                    return my_res.to_dict, my_res.code

                params = {'id': manifest_id}
                response = requests.delete(ConfigClass.METADATA_SERVICE + 'template/', params=params)
                if response.status_code != 200:
                    my_res.set_code(EAPIResponseCode.internal_error)
                    my_res.set_error_msg('Failed to delete attribute template not found')
                    return my_res.to_dict, my_res.code

                my_res.set_code(EAPIResponseCode.success)
                my_res.set_result('success')
                return my_res.to_dict, my_res.code
            except Exception as e:
                _logger.error(
                    f'Error when calling metadata service: {str(e)}')
                error_msg = {
                    'result': str(e)
                }
                return error_msg, 500

    class FileAttributes(Resource):
        """Update attributes of template attached to a file."""

        @jwt_required()
        def put(self, file_geid):
            api_response = APIResponse()
            entity = get_entity_by_id(file_geid)
            if entity['extended']['extra'].get('attributes'):
                template_id = list(entity['extended']['extra']['attributes'].keys())[0]
            else:
                raise APIException(
                    status_code=EAPIResponseCode.bad_request.value,
                    error_msg="File doesn't have an attached template"
                )
            # Permissions check
            if current_identity['role'] != 'admin':
                if entity['owner'] != current_identity['username']:
                    api_response.set_code(EAPIResponseCode.forbidden)
                    api_response.set_result('Permission Denied')
                    return api_response.to_dict, api_response.code

            if entity["zone"] == 0:
                zone = 'greenroom'
            else:
                zone = 'core'
            if not has_permission(entity['container_code'], 'file_attribute', zone, 'update'):
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result('Permission Denied')
                return api_response.to_dict, api_response.code

            try:
                params = {'id': entity['id']}
                attributes_update = request.get_json()
                payload = {
                    'parent': entity['parent'],
                    'parent_path': entity['parent_path'],
                    'type': 'file',
                    'tags': entity['extended']['extra']['tags'],
                    'system_tags': entity['extended']['extra']['system_tags'],
                    'attribute_template_id': template_id,
                    'attributes': attributes_update

                }
                response = requests.put(
                    ConfigClass.METADATA_SERVICE + 'item/', params=params, json=payload)
                res = response.json()
                res['result']['zone'] = zone
                res['result'].pop('extended')
                res['result']['manifest_id'] = template_id
                res['result'] = {**res['result'],
                                 **{f'attr_{attr}': attributes_update[attr] for attr in attributes_update}}

                return res, response.status_code
            except Exception as e:
                _logger.error(
                    f'Error when calling metadata service: {str(e)}')
                error_msg = {
                    'result': str(e)
                }
                return error_msg, 500

    class ImportManifest(Resource):
        """Import attribute template from portal as JSON."""

        @jwt_required()
        @permissions_check('file_attribute_template', '*', 'import')
        def post(self):
            data = request.get_json()
            try:

                payload = {
                    'name': data['name'],
                    'project_code': data['project_code'],
                    'attributes': data['attributes']
                }
                response = requests.post(
                    ConfigClass.METADATA_SERVICE + 'template/', json=payload)
                res = response.json()
                res['result'] = 'Success'
                return res, response.status_code
            except Exception as e:
                _logger.error(
                    f'Error when calling metadata service: {str(e)}')
                error_msg = {
                    'result': str(e)
                }
                return error_msg, 500

    class FileManifestQuery(Resource):
        """List template attributes for files."""

        @jwt_required()
        def post(self):
            api_response = APIResponse()
            data = request.get_json()
            if 'geid_list' not in data:
                api_response.set_code(EAPIResponseCode.bad_request)
                api_response.set_result('Missing required field: geid_list')
                return api_response.to_dict, api_response.code

            geid_list = data.get('geid_list')
            lineage_view = data.get('lineage_view')
            results = {}
            try:
                for geid in geid_list:
                    entity = get_entity_by_id(geid)
                    entity_attributes = entity['extended']['extra'].get('attributes')
                    if entity_attributes:
                        template_id = list(entity['extended']['extra']['attributes'].keys())[0]
                        if not has_permissions(template_id, entity) and not lineage_view:
                            api_response.set_code(EAPIResponseCode.forbidden)
                            api_response.set_result('Permission denied')
                            return api_response.to_dict, api_response.code
                        if entity['zone'] == 0:
                            zone = 'greenroom'
                        else:
                            zone = 'core'
                        if not has_permission(entity['container_code'], 'file_attribute_template', zone, 'view'):
                            api_response.set_code(EAPIResponseCode.forbidden)
                            api_response.set_result('Permission Denied')
                            return api_response.to_dict, api_response.code
                        response = requests.get(ConfigClass.METADATA_SERVICE + f'template/{template_id}/')
                        if response.status_code != 200:
                            api_response.set_code(EAPIResponseCode.not_found)
                            api_response.set_error_msg('Attribute template not found')
                            return api_response.to_dict, api_response.code
                        else:
                            attributes = []
                            extended_id = entity['extended']['id']
                            template_info = response.json()['result']
                            template_name = template_info['name']
                            for attr, value in entity_attributes[template_id].items():
                                attr_info = next(item for item in template_info['attributes'] if item['name'] == attr)
                                attribute = {
                                    'id': extended_id,
                                    'name': attr,
                                    'manifest_name': template_name,
                                    'value': value,
                                    'type': attr_info['type'],
                                    'optional': attr_info['optional'],
                                    'manifest_id': template_id,
                                }
                                attributes.append(attribute)
                        results[geid] = attributes
                    else:
                        results[geid] = {}

                api_response.set_code(EAPIResponseCode.success)
                api_response.set_result(results)
                return api_response.to_dict, api_response.code
            except Exception as e:
                _logger.error(f'Error when calling metadata service: {str(e)}')
                error_msg = {'result': str(e)}
                return error_msg, 500

    class AttachAttributes(Resource):
        """Attach attributes to files or folders (bequeath)"""

        @jwt_required()
        def post(self):
            api_response = APIResponse()
            required_fields = ['manifest_id', 'item_ids', 'attributes', 'project_code']
            data = request.get_json()
            payload = {'items': []}
            responses = {'result': []}
            # Check required fields
            for field in required_fields:
                if field not in data:
                    api_response.set_code(EAPIResponseCode.bad_request)
                    api_response.set_result(f'Missing required field: {field}')
                    return api_response.to_dict, api_response.code
            item_ids = data.get('item_ids')
            project_code = data.get('project_code')
            items = []
            updated_items = []
            try:
                if current_identity['role'] != 'admin':
                    project_role = get_project_role(project_code)
                    if not project_role:
                        api_response.set_code(EAPIResponseCode.forbidden)
                        api_response.set_result('User does not have access to this project')
                        return api_response.to_dict, api_response.code

                    for item in item_ids:
                        entity = get_entity_by_id(item)
                        root_folder = entity['parent_path'].split('.')[0]
                        zone = 'core' if entity['zone'] == 1 else 'greenroom'
                        if project_role == 'collaborator':
                            if zone == 'greenroom' and root_folder != current_identity['username']:
                                api_response.set_code(EAPIResponseCode.forbidden)
                                api_response.set_result('Permission denied')
                                return api_response.to_dict, api_response.code
                        elif project_role == 'contributor':
                            if root_folder != current_identity['username']:
                                api_response.set_code(EAPIResponseCode.forbidden)
                                api_response.set_result('Permission denied')
                                return api_response.to_dict, api_response.code
                        items.append(entity)
                else:
                    for item in item_ids:
                        entity = get_entity_by_id(item)
                        items.append(entity)
                for item in items:
                    if item['type'] == 'folder':
                        parent_path = item['parent_path']
                        name = item['name']
                        # get all items in folder recursively:
                        params = {'container_code': project_code, 'zone': item['zone'], 'recursive': True,
                                  'archived': False,
                                  'type': 'file', 'owner': item['owner'], 'parent_path': f'{parent_path}.{name}'}
                        response = requests.get(ConfigClass.METADATA_SERVICE + 'items/search/', params=params)
                        if response.status_code != 200:
                            api_response.set_code(EAPIResponseCode.internal_error)
                            api_response.set_error_msg('Failed to search for items')
                            return api_response.to_dict, api_response.code
                        else:
                            items_found = response.json()['result']
                            for found in items_found:
                                if data['manifest_id'] in found['extended']['extra']['attributes']:
                                    responses['result'].append({'name': found['name'], 'geid': found['id'],
                                                                'operation_status': 'TERMINATED',
                                                                'error_type': 'attributes_duplicate'})
                                else:
                                    updated_items.append(found)
                    else:
                        updated_items.append(item)

                if updated_items:
                    file_ids = []
                    for updated in updated_items:
                        update = {
                            'parent': updated['parent'],
                            'parent_path': updated['parent_path'],
                            'tags': updated['extended']['extra']['tags'],
                            'system_tags': updated['extended']['extra']['system_tags'],
                            'type': updated['type'],
                            'attribute_template_id': data['manifest_id'],
                            'attributes': data['attributes']
                        }
                        payload['items'].append(update)
                        file_ids.append(updated['id'])

                    params = {'ids': file_ids}
                    response = requests.put(
                        ConfigClass.METADATA_SERVICE + 'items/batch/', params=params, json=payload)
                    if response.status_code != 200:
                        _logger.error('Attaching attributes failed: {}'.format(response.text))
                        api_response.set_code(response.status_code)
                        api_response.set_result(response.text)
                        return api_response.to_dict, api_response.code
                    for item in response.json()['result']:
                        responses['result'].append({'name': item['name'], 'geid': item['id'],
                                                    'operation_status': 'SUCCEED'})

                responses['total'] = len(responses['result'])
                api_response.set_result(responses)
                return api_response.to_dict, api_response.code
            except Exception as e:
                _logger.error(f'Error when calling metadata service: {str(e)}')
                api_response.set_code(EAPIResponseCode.forbidden)
                api_response.set_result(f'Error when calling metadata service: {str(e)}')
                return api_response.to_dict, api_response.code
