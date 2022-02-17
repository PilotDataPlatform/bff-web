from flask import request, render_template
import requests
import os
import json
import re
import datetime
from flask_jwt import jwt_required, current_identity
from resources.decorator import check_role, check_user
from resources.utils import *
from flask_restx import Resource
from .namespace import users_entity_ns, datasets_entity_ns
from resources.swagger_modules import user_module, new_user_module, user_sample_return, users_sample_return
from resources.swagger_modules import permission_return, success_return
from resources.swagger_modules import dataset_sample_return, datasets_sample_return, dataset_user_status
from config import ConfigClass
from services.invitation_services.invitation_manager import SrvInvitationManager
from models.invitation import InvitationForm
from services.notifier_services.email_service import SrvEmail
from services.logger_services.logger_factory_service import SrvLoggerFactory
from services.container_services.container_manager import SrvContainerManager
from services.neo4j_service.neo4j_client import Neo4jClient
from models.user_type import map_neo4j_to_frontend
from services.permissions_service.decorators import permissions_check

# init logger
_logger = SrvLoggerFactory('api_user_ops').get_logger()


class Users(Resource):
    @users_entity_ns.expect(user_module)
    @users_entity_ns.response(200, user_sample_return)
    @jwt_required()
    @permissions_check('invite', '*', 'create')
    def post(self):
        '''
        This method allow site admin to invite a user.
        '''
        try:
            # Fetch payload
            post_data = request.get_json()
            _logger.info(
                'Call API for inviting a user to platform: {}'.format(post_data))

            username = post_data.get("name", None)
            password = post_data.get("password", None)
            first_name = post_data.get("first_name", None)
            last_name = post_data.get("last_name", None)
            email = post_data.get("email", None)
            role = post_data.get("role", None)
            access_token = request.headers.get("Authorization", None)

            if not username or not password or not first_name or not last_name:
                _logger.error(
                    'Field username/password/first_name/last_name  is required.')
                return {'result': 'missing username, password, first name or last name'}, 400

            if not access_token:
                _logger.error('Valid token is required')
                return {'result': 'missing valid token'}, 400

            # since keycloak will change the uppercase into lower so enforce lowercase here
            if any([x.isupper() for x in username]):
                _logger.error('Username must be all lowercase')
                return {'result': 'username must be all lowercase'}, 403

            # Create a user in keycloak
            # TODO: remove admin password in the payload
            url = ConfigClass.KONG_BASE + "portal/admin/users"
            headers = {
                'Authorization': access_token
            }
            payload = {
                "admin_username": "admin",
                "admin_password": "amenamen",
                "realm": ConfigClass.KEYCLOAK_REALM,
                "username": username,
                "password": password,
                "email": email,
                "firstname": first_name,
                "lastname": last_name
            }

            res = requests.post(
                url=url,
                headers=headers,
                json=payload
            )

            if res.status_code == 401:
                return {'result': 'Permission Denied'}, 401
            elif res.status_code >= 400:
                _logger.error('Failed to add user to keycloak')
                return {'result': 'fail to add user to keycloak.'}

            # Create user node and default dataset node in neo4j
            post_data.pop("password", None)
            post_data['path'] = "users"
            post_data["global_entity_id"] = fetch_geid("user")
            if (role is None):
                post_data['role'] = "member"
            url = ConfigClass.NEO4J_SERVICE + "nodes/User"
            headers = {
                'Authorization': access_token
            }
            res = requests.post(
                url=url,
                headers=headers,
                json=post_data
            )
            if (res.status_code != 200):
                _logger.error('Failed to add user node to neo4j: {}'.format(
                    json.loads(res.text)))
                return {'result': json.loads(res.text)}, res.status_code

        except Exception as e:
            _logger.error(
                'Error in inviting user to platform: {}'.format(str(e)))
            return {'result': str(e)}, 403

        return {'result': json.loads(res.text)}, 200

    @users_entity_ns.response(200, users_sample_return)
    @jwt_required()
    @permissions_check('users', '*', 'view')
    def get(self):
        '''
        This method allow user to fetch all registered users in the platform.
        '''
        _logger.info(
            'Call API for to admin fetching all users in the platform')
        try:

            # Fetch all user nodes from neo4j
            url = ConfigClass.NEO4J_SERVICE + "nodes/User/query"
            query_data = {
                **request.args,
            }
            if not request.args.get("status"):
                query_data["status"] = ["active", "disabled"]
            response = neo4j_query_with_pagination(
                url, query_data, partial=True)
            # result = response.to_dict["result"]

            # Convert UTC to timezone in the config for time_created and time_modified
            # for obj in result:
            #     if obj.get("time_created"):
            #         obj["time_created"] = convert_from_utc(obj["time_created"])
            #     if obj.get("time_modified"):
            #         obj["time_modified"] = convert_from_utc(obj["time_modified"])
            # response.set_result(result)

            if (response.code != 200):
                _logger.error('Failed to fetch info in neo4j: {}'.format(
                    "users operation line 148, uncatched error"))
                return response.to_dict

        except Exception as e:
            _logger.error('Error in fetching all users: {}'.format(str(e)))
            return {'Error': str(e)}, 403

        return response.to_dict


class ContainerAdmins(Resource):
    @datasets_entity_ns.response(200, users_sample_return)
    @jwt_required()
    @permissions_check('project', '*', 'view')
    def get(self, project_geid):
        '''
        This method allow user to fetch all admins under a specific dataset with permissions.
        '''
        # check dataset exists
        container_mgr = SrvContainerManager()
        query_params = {"global_entity_id": project_geid}
        container_id = get_container_id(query_params)
        try:
            my_project = container_mgr.check_container_exist(
                None, "Container", container_id)
            if len(my_project) == 0:
                return {'result': 'Container %s is not available.' % container_id}, 404
        except Exception as e:
            _logger.error(
                'Container %s is not available.' % container_id)
            return {'result': str(e)}, 404

        # fetch admins of the project
        url = ConfigClass.NEO4J_SERVICE + 'relations/query'
        try:
            res = requests.post(
                url=url,
                json={
                    'start_label': 'User',
                    'end_label': 'Container',
                    'end_params': {'code': my_project[0]['code']},
                    'start_params': {'status': 'active'},
                    'label': 'admin'
                }
            )
            if (res.status_code != 200):
                _logger.error('Calling neo4j service %s.' % str(res.text))
                return {'result': json.loads(res.text)}, res.status_code
        except Exception as e:
            _logger.error('Calling neo4j service %s.' % str(e))
            return {'result': str(e)}, res.status_code

        # format response
        result = []
        for x in json.loads(res.text):
            temp = x['start_node']
            temp["permission"] = x['r']['type']
            result.append(temp)

        return {"result": result}


class ContainerUsers(Resource):

    @datasets_entity_ns.response(200, users_sample_return)
    @jwt_required()
    @permissions_check('users', '*', 'view')
    # def get(self, dataset_id):
    def get(self, project_geid):
        '''
        This method allow user to fetch all users under a specific dataset with permissions.
        '''
        _logger.info(
            'Calling API for fetching all users under dataset {}'.format(str(project_geid)))

        try:

            # Get token from reuqest's header
            access_token = request.headers.get('Authorization', None)
            headers = {
                'Authorization': access_token
            }
            query_params = {"global_entity_id": project_geid}
            container_id = get_container_id(query_params)
            # Check if dataset exist
            url = ConfigClass.NEO4J_SERVICE + 'nodes/Container/node/' + container_id
            res = requests.get(
                url=url,
                headers=headers
            )
            datasets = json.loads(res.text)
            if (len(datasets) == 0):
                _logger.error(
                    'Container %s is not available.' % container_id)
                return {'result': 'Container %s is not available.' % container_id}, 404

            # Fetch all users under the dataset
            url = ConfigClass.NEO4J_SERVICE + 'relations/query'
            payload = {
                'start_label': 'User',
                'end_label': 'Container',
                'end_params': {'code': datasets[0]['code']},
                'start_params': {'status': 'active'},
            }
            res = requests.post(
                url=url,
                headers=headers,
                json=payload
            )

            if (res.status_code != 200):
                _logger.error(
                    'Calling neo4j service %s.' % str(res.text))
                return {'result': json.loads(res.text)}, res.status_code

            # Format response
            result = []
            for x in json.loads(res.text):
                temp = x['start_node']
                temp["permission"] = x['r']['type']
                result.append(temp)

        except Exception as e:
            _logger.error(
                'Error in fetching all users under a specific dataset: {}'.format(str(e)))
            return {'result': str(e)}, 403

        return {"result": result}

    # deprecate?
    @datasets_entity_ns.response(200, success_return)
    @jwt_required()
    @check_role("admin")
    def post(self, project_geid):
        '''
        This method allow user to bulk add users to a specific dataset with permissions.
        '''
        _logger.info(
            'Calling API for bulk adding users to dataset {}'.format(str(project_geid)))

        try:
            # Get token from reuqest's header
            access_token = request.headers.get("Authorization", None)
            headers = {
                'Authorization': access_token
            }
            query_params = {"global_entity_id": project_geid}
            container_id = get_container_id(query_params)

            # Check if dataset exist
            url = ConfigClass.NEO4J_SERVICE + "nodes/Container/node/" + container_id
            res = requests.get(
                url=url,
                headers=headers
            )
            datasets = json.loads(res.text)
            if (len(datasets) == 0):
                _logger.error(
                    'Container %s is not available.' % container_id)
                return {'result': "Container %s is not available." % container_id}, 404

            if ('type' in datasets[0] and datasets[0]['type'] == "default"):
                _logger.error(
                    'Container %s is default.' % container_id)
                return {'result': 'Container %s is default.' % container_id}, 403

            # then start to get the added user
            post_data = request.get_json()
            users = post_data.get("users", [])
            role = post_data.get("role", "member")
            error = bulk_add_user(headers, container_id, users, role)
            if len(error) != 0:
                return {"result": str(error)}

        except Exception as e:
            _logger.error('Error in bulk adding user: {}'.format(str(e)))
            return {'result': str(e)}, 403

        return {"result": "success"}, 200


class UserContainerQuery(Resource):

    @users_entity_ns.response(200, permission_return)
    # @ jwt_required()
    # @ check_user()
    def post(self, username):
        '''
        This method allow user to get the user's permission towards all containers (except default).
        '''
        _logger.info('Call API for fetching user {} role towards all projects'.format(
            username))
        try:
            # Check if user is admin
            url = ConfigClass.NEO4J_SERVICE + "nodes/User/query"
            res = requests.post(
                url=url,
                json={"name": username}
            )
            users = json.loads(res.text)
            if (len(users) == 0):
                _logger.error("User %s does not exist." % username)
                return {'result': "User %s does not exist." % username}, 404
            user_node = users[0]
            user_role = user_node['role']

            data = request.get_json()
            payload = {
                "extra_query": "where r.status <> 'hibernate' OR r.status IS NULL with * ",
                "start_label": "User",
                "end_label": "Container",
                "start_params": data.get("start_params", None),
                "end_params": data.get("end_params", None),
                "partial": True,
                "page": data.get("page", 0),
                "page_size": data.get("page_size", None),
                "order_by": data.get("order_by", None),
                "order_type": data.get("order_type", None),
                "order_node": "end_node",
            }

            if payload["end_params"] and "create_time_start" in payload["end_params"] and "create_time_end" in payload[
                    "end_params"]:
                payload["end_params"]["create_time_start"] = datetime.datetime.utcfromtimestamp(
                    int(payload["end_params"]["create_time_start"])).strftime('%Y-%m-%dT%H:%M:%S')
                payload["end_params"]["create_time_end"] = datetime.datetime.utcfromtimestamp(
                    int(payload["end_params"]["create_time_end"])).strftime('%Y-%m-%dT%H:%M:%S')

            if user_role != "admin":
                if not payload["start_params"]:
                    payload["start_params"] = {}
                    payload["start_params"]["id"] = user_node["id"]
                url = ConfigClass.NEO4J_SERVICE + "relations/query"
                response = neo4j_query_with_pagination(
                    url, payload, partial=True)
                if (response.code != 200):
                    _logger.error('Failed to fetch info in neo4j: {}'.format(
                        json.loads(res.text)))
                    return response.to_dict
                result = []
                for x in response.result:
                    temp = {
                        # "id": x['end_node']['id'],
                        # "name": x['end_node']['name'],
                        # "code": x['end_node']['code'],
                        "permission": x['r']['type'],
                        **x['end_node']
                    }
                    result.append(temp)

                response.set_result(result)
                response.set_response("role", user_role)
                return response.to_dict
            else:
                payload = {
                    "page": data.get("page", 0),
                    "page_size": data.get("page_size", None),
                    "order_by": data.get("order_by", None),
                    "order_type": data.get("order_type", None),
                    **data.get("end_params", {})
                }
                url = ConfigClass.NEO4J_SERVICE + "nodes/Container/query"
                response = neo4j_query_with_pagination(
                    url, payload, partial=True)
                if (response.code != 200):
                    _logger.error('Failed to fetch info in neo4j: {}'.format(
                        json.loads(res.text)))
                    return response.to_dict

                result = []
                for x in response.result:
                    dataset_type = x.get("type", None)
                    if dataset_type and dataset_type != "default":
                        # temp = {
                        #     "container_id": x['id'],
                        #     "container_name": x['name'],
                        #     "code": x['code'],
                        #     "permission": "admin"
                        # }
                        # result.append(temp)
                        x["permission"] = "admin"
                        result.append(x)
                response.set_result(result)
                response.set_response("role", user_role)
                return response.to_dict

        except Exception as e:
            _logger.error(
                'Error in fetching user\'s role towards all projects: {}'.format(str(e)))
            # raise e
            return {'result': str(e)}, 500

        # return {'result': {
        #     "role": user_role,
        #     "permission": result
        # }}, 200


# Deprecate
class UserDefaultContainer(Resource):
    @users_entity_ns.response(200, datasets_sample_return)
    @jwt_required()
    @check_user()
    def get(self, username):
        '''
        This method allow user to get the user's default dataset.
        '''
        try:
            # Get token from reuqest's header
            access_token = request.headers.get("Authorization", None)
            headers = {
                'Authorization': access_token
            }

            # Fetch default dataset that connected to the user
            url = ConfigClass.NEO4J_SERVICE + "relations/query"
            payload = {
                "label": "admin",
                "start_label": "User",
                "end_label": "Container",
                "start_params": {"name": username},
                "end_params": {"type": "default"}
            }
            res = requests.post(
                url=url,
                headers=headers,
                json=payload
            )
            result = json.loads(res.text)
            if (len(result) == 0):
                return {'result': []}, 200

            # Format response
            result = [x['end_node'] for x in json.loads(res.text)]

        except Exception as e:
            return {'result': str(e)}, 403

        return {'result': result}, 200

    @users_entity_ns.response(200, dataset_sample_return)
    @jwt_required()
    @check_user()
    def post(self, username):
        '''
        This method allow user to create the default dataset.
        '''
        try:
            # Get token from reuqest's header
            access_token = request.headers.get("Authorization", None)
            headers = {
                'Authorization': access_token
            }

            # Check if user is existed
            url = ConfigClass.NEO4J_SERVICE + "nodes/User/query"
            res = requests.post(
                url=url,
                headers=headers,
                json={"name": username}
            )
            users = json.loads(res.text)
            if (len(users) == 0):
                return {'result': "User %s does not exist." % username}, 404
            user_id = users[0]['id']

            # create a default dataset node
            url = ConfigClass.NEO4J_SERVICE + "nodes/Container"
            default_name = username + "_default"
            payload = {
                "name": default_name,
                "type": "default",
                "parent_id": user_id,
                "parent_relation": "admin",
                "path": default_name
            }
            neo_res = requests.post(
                url=url,
                headers=headers,
                json=payload
            )
            if (neo_res.status_code != 200):
                return {'result': json.loads(neo_res.text)}, res.status_code

            # Create folder in NFS
            url = ConfigClass.DATA_SERVICE + "folders"
            payload = {
                "path": os.path.join("users", default_name)
            }
            res = requests.post(
                url=url,
                json=payload
            )
            if (res.status_code != 200):
                return {'result': json.loads(res.text)}, res.status_code

        except Exception as e:
            return {'Error': str(e)}, 403

        return {'result': json.loads(neo_res.text)}, 200


class ContainerUsersQuery(Resource):
    @jwt_required()
    @permissions_check('users', '*', 'view')
    def post(self, project_geid):
        _logger.info(
            'Call API for fetching all users in a dataset')
        try:
            access_token = request.headers.get('Authorization', None)
            headers = {
                'Authorization': access_token
            }
            query_params = {"global_entity_id": project_geid}
            container_id = get_container_id(query_params)
            # Check if dataset exist
            url = ConfigClass.NEO4J_SERVICE + 'nodes/Container/node/' + container_id
            res = requests.get(
                url=url,
                headers=headers
            )
            datasets = json.loads(res.text)

            # Fetch all users under the dataset
            url = ConfigClass.NEO4J_SERVICE + 'relations/query'
            payload = {
                'start_label': 'User',
                'end_label': 'Container',
                'end_params': {'id': datasets[0]['id']},
                'sort_node': 'start',
                **request.get_json()
            }
            if not "start_params" in payload:
                payload["start_params"] = {}
            payload["start_params"]["status"] = "active"
            response = neo4j_query_with_pagination(url, payload, partial=True)
            if (response.code != 200):
                _logger.error('Failed to fetch info in neo4j: {}'.format(
                    json.loads(res.text)))
                return response.to_dict

            result = []
            for x in response.result:
                temp = x['start_node']
                temp["permission"] = x['r']['type']
                temp["project_status"] = x['r'].get("status")
                # correct timezone
                # if temp.get("time_created"):
                #     temp["time_created"] = convert_from_utc(temp["time_created"])
                # if temp.get("time_modified"):
                #     temp["time_modified"] = convert_from_utc(temp["time_modified"])
                result.append(temp)
            response.set_result(result)
            return response.to_dict
        except Exception as e:
            return {'Error': str(e)}, 403

