from flask import request
from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
import requests
import json
import datetime
from resources.utils import *
from resources.decorator import check_role
from resources.utils import check_container_exist
from resources.swagger_modules import dataset_module, dataset_sample_return, datasets_sample_return
from services.container_services.container_manager import SrvContainerManager
from .namespace import datasets_entity_ns
from config import ConfigClass
from services.logger_services.logger_factory_service import SrvLoggerFactory
from services.permissions_service.decorators import permissions_check

# init logger
_logger = SrvLoggerFactory('api_dataset_ops').get_logger()


# this class is the action on all datasets
class Containers(Resource):
    @datasets_entity_ns.response(200, datasets_sample_return)
    @jwt_required()
    # @check_role("visitor")
    def get(self):
        '''
        This method allow user list all datasets/metadatas/tags
        '''
        try:
            param = request.args.get('type', None)  # metadata/tag/usecase
            tags = request.args.get('tags', None)
            _logger.info(
                'Call API for fetching project info: type {}'.format(param))
            access_token = request.headers.get("Authorization", None)

            result = None
            if(param == "metadata" or param == "tag"):
                res = retreive_property(access_token, "Container")

                if(param == "tag"):
                    result = list(set().union(*res['tags']))
                else:
                    result = {}
                    for key, value in res.items():
                        if key.startswith('_'):
                            result[key] = value
            else:
                role = current_identity["role"]
                username = current_identity["username"]
                payload = {**request.args}
                if role != "admin":
                    payload["discoverable"] = True

                if "create_time_start" in payload and "create_time_end" in payload:
                    payload["create_time_start"] = datetime.datetime.utcfromtimestamp(int(payload["create_time_start"])).strftime('%Y-%m-%dT%H:%M:%S')
                    payload["create_time_end"] = datetime.datetime.utcfromtimestamp(int(payload["create_time_end"])).strftime('%Y-%m-%dT%H:%M:%S')
               
                url = ConfigClass.NEO4J_SERVICE + "nodes/Container/query"
                response = neo4j_query_with_pagination(url, payload, partial=True)

                if(response.code != 200):
                    _logger.error('Failed to fetch info in neo4j: {}'.format(
                        json.loads(response.result)))
                    return response.to_dict

                _logger.info('success in calling neo4j')

                return response.to_dict
        except Exception as e:
            _logger.error('Error in fetching project info: {}'.format(str(e)))
            return {'result': 'Error %s' % str(e)}, 403


class Container(Resource):
    @datasets_entity_ns.response(200, dataset_sample_return)
    @jwt_required()
    @permissions_check('project', '*', 'update')
    def put(self, project_geid):
        '''
        This method allow to allow admin to update information of the container.
        '''

        try:
            post_data = request.get_json()
            _logger.info('Calling API for updating project info: project_geid {}, {}'.format(
                project_geid, post_data))

            # Check if the dataset exists
            access_token = request.headers.get("Authorization", None)
            query_params = {"global_entity_id": project_geid}
            dataset_id = get_container_id(query_params)
            datasets = check_container_exist(
                access_token, "Container", dataset_id)
            if len(datasets) == 0:
                _logger.error('Field dataset_id is not valid.')
                return {'result': "Dataset %s is not available." % project_geid}, 403

            if post_data.get("icon"):
                # check if icon is bigger then limit
                if len(post_data.get("icon")) > ConfigClass.ICON_SIZE_LIMIT:
                    return {'result': 'icon to large'}, 413

            # Update dataset properties
            result = requests.put(
                ConfigClass.NEO4J_SERVICE+"nodes/Container/node/%s" % dataset_id, json=post_data)

            # If we get the error in the result as 403
            if result.status_code == 403:
                raise Exception(json.loads(result.text))

        except Exception as e:
            _logger.error(
                'Error in updating project information:{}'.format(str(e)))
            return {'result': str(e)}, 403

        return {'result': json.loads(result.text)}, 200


def get_container_id(query_params):
    url = ConfigClass.NEO4J_SERVICE + f"nodes/Container/query"
    payload = {
        **query_params
    }
    result = requests.post(url, json=payload)
    if result.status_code != 200 or result.json() == []:
        return None
    result = result.json()[0]
    container_id = result["id"]
    return str(container_id)
