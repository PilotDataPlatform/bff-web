from config import ConfigClass
from flask_jwt import jwt_required, current_identity
from models.api_response import APIResponse, EAPIResponseCode
from common import LoggerFactory
from services.permissions_service.decorators import permissions_check
from .utils import get_collection_by_id
from flask_restx import Resource
import requests
from flask import request
import json

_logger = LoggerFactory('api_files_ops_v1').get_logger()


class VirtualFolderFiles(Resource):

    @jwt_required()
    def post(self, collection_geid):
        """
        Add items to vfolder
        """
        _res = APIResponse()

        try:
            # Get collection
            vfolder = get_collection_by_id(collection_geid)
            if current_identity["role"] != "admin":
                if vfolder["owner"] != current_identity["username"]:
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result("no permission for this project")
                    return _res.to_dict, _res.code

            data = request.get_json()
            data['id'] = collection_geid
            url = f'{ConfigClass.METADATA_SERVICE}collection/items/'
            response = requests.post(url, json=data)
            if response.status_code != 200:
                _logger.error('Failed to add items to collection:   ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result("Failed to add items to collection")
                return _res.to_dict, _res.code
            else:
                _logger.info('Successfully add items to collection: {}'.format(json.dumps(response.json())))
                return response.json()

        except Exception as e:
            _logger.error("errors in add items to collection: {}".format(str(e)))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to add items to collection")
            return _res.to_dict, _res.code

    @jwt_required()
    def delete(self, collection_geid):
        """
        Delete items from vfolder
        """

        _res = APIResponse()

        try:
            # Get collection
            vfolder = get_collection_by_id(collection_geid)
            if current_identity["role"] != "admin":
                if vfolder["owner"] != current_identity["username"]:
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result("no permission for this project")
                    return _res.to_dict, _res.code

            data = request.get_json()
            data['id'] = collection_geid
            url = f'{ConfigClass.METADATA_SERVICE}collection/items/'
            response = requests.delete(url, json=data)
            if response.status_code != 200:
                _logger.error('Failed to remove items from collection:   ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result("Failed to remove items from collection")
                return _res.to_dict, _res.code

            else:
                _logger.info('Successfully remove items from collection: {}'.format(json.dumps(response.json())))
                return response.json()

        except Exception as e:
            _logger.error("errors in remove items from collection: {}".format(str(e)))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to remove items from collection")
            return _res.to_dict, _res.code

    @jwt_required()
    def get(self, collection_geid):

        """
        Get items from vfolder
        """
        _res = APIResponse()

        try:
            # Get collection
            vfolder = get_collection_by_id(collection_geid)
            if current_identity["role"] != "admin":
                if vfolder["owner"] != current_identity["username"]:
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result("no permission for this project")
                    return _res.to_dict, _res.code

            url = f'{ConfigClass.METADATA_SERVICE}collection/items/'
            params = {'id': collection_geid}
            response = requests.get(url, params=params)
            if response.status_code != 200:
                _logger.error('Failed to get items from collection:   ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result("Failed to get items from collection")
                return _res.to_dict, _res.code
            else:
                _logger.info('Successfully retrieved items from collection: {}'.format(json.dumps(response.json())))
                return response.json()

        except Exception as e:
            _logger.error("errors in retrieve items to collection: {}".format(str(e)))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to retrieve items from collection")
            return _res.to_dict, _res.code


class VirtualFolder(Resource):

    @jwt_required()
    @permissions_check('collections', 'core', 'view')
    def get(self):
        payload = {
            "owner": current_identity['username'],
            'container_code': request.args.get('project_code')
        }
        response = requests.get(f'{ConfigClass.METADATA_SERVICE}collection/search/', params=payload)
        return response.json(), response.status_code

    @jwt_required()
    @permissions_check('collections', 'core', 'create')
    def post(self):
        payload = {
            "owner": current_identity['username'],
            **request.get_json(),
            'container_code': request.args.get('project_code'),
        }
        payload['container_code'] = payload.pop('project_code')
        response = requests.post(f'{ConfigClass.METADATA_SERVICE}collection/', json=payload)
        return response.json(), response.status_code


class VirtualFolderInfo(Resource):
    @jwt_required()
    def delete(self, collection_geid):
        _res = APIResponse()

        try:
            # Get collection
            vfolder = get_collection_by_id(collection_geid)

            if current_identity["role"] != "admin":
                if vfolder["owner"] != current_identity["username"]:
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_result("no permission for this project")
                    return _res.to_dict, _res.code

            url = f'{ConfigClass.METADATA_SERVICE}collection/'
            params = {'id': collection_geid}
            response = requests.delete(url, params=params)
            if response.status_code != 200:
                _logger.error('Failed to delete collection:   ' + response.text)
                _res.set_code(EAPIResponseCode.internal_error)
                _res.set_result("Failed to delete collection")
                return _res.to_dict, _res.code
            else:
                _logger.info(f'Successfully delete collection: {collection_geid}')
                return response.json()
        except Exception as e:
            _logger.error("errors in delete collection: {}".format(str(e)))
            _res.set_code(EAPIResponseCode.internal_error)
            _res.set_result("Failed to delete collection")
            return _res.to_dict, _res.code
