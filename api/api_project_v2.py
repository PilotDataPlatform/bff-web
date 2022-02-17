from flask_restx import Api, Resource, fields
from flask_jwt import jwt_required, current_identity
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from models.api_meta_class import MetaAPI
from services.logger_services.logger_factory_service import SrvLoggerFactory
from services.container_services.container_manager import SrvContainerManager
from services.neo4j_service.neo4j_client import Neo4jClient
from services.permissions_service.decorators import permissions_check
from api import module_api
from flask import request
import json
import requests
import ldap
import re
import os
import ldap.modlist as modlist
from resources.utils import bulk_add_user, fetch_geid, add_user_to_ad_group, add_admin_to_project_group, \
    assign_project_role
from minio.sseconfig import Rule
from minio.sseconfig import SSEConfig
from minio.versioningconfig import ENABLED
from minio.versioningconfig import VersioningConfig
from resources.minio import Minio_Client
from resources.minio import create_admin_policy
from resources.minio import create_collaborator_policy
from resources.minio import create_contributor_policy

api_ns_projects = module_api.namespace(
    'Project Restful', description='For project feature', path='/v1')
api_ns_project = module_api.namespace(
    'Project Restful', description='For project feature', path='/v1')

_logger = SrvLoggerFactory('api_project').get_logger()
'''
-> duplicate_check()
    -> create_container_node()
        -> add_admins()
            -> create_minio_bucket
              -> ldap_create_user_group
                -> neo4j_add_platform_admins
                  -> keyclock_create_roles()
                    -> keyclock_add_group_role()
                      -> create_username_folder()
'''


class APIProjectV2(metaclass=MetaAPI):
    '''
    [POST]/projects
    [GET]/projects
    [GET]/project/<project_id>
    '''

    def api_registry(self):
        api_ns_projects.add_resource(self.RestfulProjectsv2, '/projects')

    class RestfulProjectsv2(Resource):
        def get(self):
            # init resp
            my_res = APIResponse()
            return my_res.to_dict, my_res.code

        @jwt_required()
        @permissions_check('project', '*', 'create')
        def post(self):
            """
            This method allow to create a new project in platform.
            Notice that top-level container could only be created by site admin.
            """
            post_data = request.get_json()
            _res = APIResponse()
            _logger.info(
                'Calling API for creating project: {}'.format(post_data))

            container_type = post_data.get("type", None)
            description = post_data.get("description", None)
            dataset_code = post_data.get("code", None)
            access_token = request.headers.get("Authorization", None)
            headers = {
                'Authorization': access_token
            }

            try:
                is_valid, message = validate_post_data(post_data)
                if not is_valid:
                    _logger.error("Invalid post data")
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_error_msg(message["result"])
                    return _res.to_dict, _res.code

                is_dataset, res_datasets, code = duplicate_check(dataset_code)
                if not is_dataset:
                    _logger.error("Duplicate project data")
                    _res.set_code(EAPIResponseCode.conflict)
                    _res.set_error_msg(res_datasets["result"])
                    return _res.to_dict, _res.code

                # let the hdfs create a dataset
                post_data.update({'path': dataset_code})
                post_data['system_tags'] = ['copied-to-core']

                # if we have the parent_id then update relationship label as PARENT
                if post_data.get('parent_id', None):
                    post_data.update({'parent_relation': 'PARENT'})
                if not post_data.get('discoverable', None):
                    post_data.update({"discoverable": True})
                is_container, container_result, code = create_container_node(
                    post_data)
                if not is_container:
                    _logger.error("Error when creating node in neo4j")
                    _res.set_code(code)
                    _res.set_error_msg("Error when creating Container node in neo4j")
                    return _res.to_dict, _res.code
                result = container_result.json()[0]

                # Add admin users relationship in neo4j
                is_valid, res = add_admins(headers, result)
                if not is_valid:
                    _logger.error("Error when adding admin into project")
                    _res.set_code(EAPIResponseCode.internal_error)
                    _res.set_error_msg(res["result"])
                    return _res.to_dict, _res.code

                # Create MinIO bucket for project with name based on zone and dataset_code
                zone = post_data.get("zone", None)
                is_created, result, status_code = create_minio_bucket(dataset_code, zone)
                if not is_created:
                    _res.set_code(status_code)
                    _res.set_error_msg(result["result"])
                    return _res.to_dict, _res.code

                # Create Project User Group in ldap
                ldap_create_user_group(dataset_code, description)

                # Add admin to new group in keycloak and assign project-admin role
                origin_users = neo4j_add_platform_admins(dataset_code)
                is_created, res, status_code = keycloak_create_roles(
                    dataset_code)
                if not is_created:
                    _logger.error("Error when creating project roles in keycloak")
                    _res.set_code(status_code)
                    _res.set_error_msg(res["result"])
                    return _res.to_dict, _res.code
                keycloak_add_group_role(dataset_code, origin_users)

                _logger.info(
                    f"Creating namespace folder for list of users in platfomr_admin_users : {origin_users}")
                # create username namespace folder for all platform admin
                bulk_create_folder_usernamespace(
                    users=origin_users, project_code=dataset_code)

            except Exception as e:
                _logger.error('Error in creating project: {}'.format(str(e)))
                _res.set_code(EAPIResponseCode.forbidden)
                _res.set_error_msg('Error %s' % str(e))
                return _res.to_dict, _res.code

            _res.set_result(container_result.json())
            return _res.to_dict, _res.code


def validate_post_data(post_data):
    name = post_data.get("name", None)
    code = post_data.get("code", None)

    for x in post_data:
        if type(post_data[x]) == dict:
            post_data.update({x: json.dumps(post_data[x])})
    if not name or not code:
        _logger.error('Field name and code field is required.')
        return False, {'result': "Error the name and code field is required"}

    project_code_pattern = re.compile(ConfigClass.PROJECT_CODE_REGEX)
    is_match = re.search(project_code_pattern, code)

    if not is_match:
        _logger.error('Project code does not match the pattern.')
        return False, {'result': "Project code does not match the pattern."}

    project_name_pattern = re.compile(ConfigClass.PROJECT_NAME_REGEX)
    is_match = re.search(project_name_pattern, name)

    if not is_match:
        _logger.error('Project name does not match the pattern.')
        return False, {'result': "Project name does not match the pattern."}

    if post_data.get("icon"):
        # check if icon is bigger then limit
        if len(post_data.get("icon")) > ConfigClass.ICON_SIZE_LIMIT:
            return False, {'result': 'icon too large'}

    return True, {}


def duplicate_check(code):
    url = ConfigClass.NEO4J_SERVICE + "nodes/Container/query"
    res = requests.post(url=url, json={"code": code})
    datasets = res.json()
    if datasets:
        return False, {'result': 'Error duplicate project code'}, 409
    return True, datasets, 200


def create_container_node(post_data):
    post_data["global_entity_id"] = fetch_geid("project")

    container_result = requests.post(
        ConfigClass.NEO4J_SERVICE + "nodes/Container",
        json=post_data
    )
    if container_result.status_code != 200:
        return False, container_result.json(), container_result.status_code
    return True, container_result, 200


def add_admins(headers, result):
    dataset_id = result.get("id")
    admins = result.get("admin", None)
    if admins is not None:
        error = bulk_add_user(headers, dataset_id, admins, "admin")
        if len(error) != 0:
            return False, {"result": str(error)}
    return True, {}


def create_minio_bucket(project_code, zone):
    try:
        # establish minio bucket prefix (gr- or core-) based on zone parameter in payload
        valid_zones = {"greenroom": "gr-", "core": "core-"}
        if zone not in valid_zones:
            raise ValueError('Invalid zone selected')
        bucket_prefix = valid_zones[zone]

        # establish bucket name
        bucket_name = bucket_prefix + project_code

        # initialize MinIO client
        mc = Minio_Client()

        # if bucket name does not already exist, create it in minio
        if not mc.client.bucket_exists(bucket_name):
            mc.client.make_bucket(bucket_name)
            mc.client.set_bucket_versioning(bucket_name, VersioningConfig(ENABLED))
            mc.client.set_bucket_encryption(
                bucket_name, SSEConfig(Rule.new_sse_s3_rule()),
            )
            _logger.info(f"MinIO bucket created: {bucket_name}")
        else:
            error_msg = "MinIO bucket already exists"
            _logger.error(error_msg)
            status_code = EAPIResponseCode.conflict
            return False, {'result': error_msg}, status_code

        # add MinIO policies for respective bucket (admin, collaborator, contributor)
        policy_name = create_admin_policy(project_code)
        stream = os.popen('mc admin policy add minio %s %s' % (project_code + "-admin", policy_name))
        policy_name = create_contributor_policy(project_code)
        stream = os.popen('mc admin policy add minio %s %s' % (project_code + "-contributor", policy_name))
        policy_name = create_collaborator_policy(project_code)
        stream = os.popen('mc admin policy add minio %s %s' % (project_code + "-collaborator", policy_name))
        _logger.info(f"MinIO policies successfully applied for: {bucket_name}")

    except Exception as e:
        error_msg = f"Error when creating MinIO bucket: {str(e)}"
        _logger.error(error_msg)
        status_code = EAPIResponseCode.internal_error
        return False, {'result': error_msg}, status_code

    return True, {}, 200


def ldap_create_user_group(code, description):
    try:
        ldap.set_option(ldap.OPT_REFERRALS, ldap.OPT_OFF)
        conn = ldap.initialize(ConfigClass.LDAP_URL)
        conn.simple_bind_s(ConfigClass.LDAP_ADMIN_DN,
                           ConfigClass.LDAP_ADMIN_SECRET)

        dn = "cn={}{},ou=Gruppen,ou={},dc={},dc={}".format(
            ConfigClass.AD_PROJECT_GROUP_PREFIX,
            code,
            ConfigClass.LDAP_OU,
            ConfigClass.LDAP_DC1,
            ConfigClass.LDAP_DC2
        )

        # NOTE here LDAP client will require the BINARY STRING for the payload
        # Please remember to convert all string to utf-8
        objectclass = [ConfigClass.LDAP_objectclass.encode('utf-8')]
        attrs = {'objectclass': objectclass,
                 'sAMAccountName': f'{ConfigClass.AD_PROJECT_GROUP_PREFIX}-{code}'.encode('utf-8')}
        if description:
            attrs['description'] = description.encode('utf-8')
        ldif = modlist.addModlist(attrs)
        conn.add_s(dn, ldif)
    except Exception as error:
        _logger.error(f"Error while creating user group in ldap : {error}")


def neo4j_add_platform_admins(code):
    url = ConfigClass.NEO4J_SERVICE + "nodes/User/query"
    users_res = requests.post(
        url=url,
        json={"role": "admin", "status": "active"}
    )
    users = users_res.json()

    # exclude the admin user
    origin_users = users
    users = [user for user in users if user['name'] != 'admin']

    access_token = request.headers.get("Authorization", None)
    for user in users:
        add_user_to_ad_group(user["email"], code, _logger, access_token)
    return origin_users


def keycloak_create_roles(code):
    payload = {
        "realm": ConfigClass.KEYCLOAK_REALM,
        "project_roles": ["admin", "collaborator", "contributor"],
        "project_code": code
    }
    keycloak_roles_url = ConfigClass.AUTH_SERVICE + 'admin/users/realm-roles'
    keycloak_roles_res = requests.post(url=keycloak_roles_url, json=payload)
    if keycloak_roles_res.status_code != 200:
        return False, {'result': 'create realm role: ' + json.loads(
            keycloak_roles_res.text)}, keycloak_roles_res.status_code
    return True, {}, 200


def keycloak_add_group_role(code, origin_users):
    for user in origin_users:
        add_admin_to_project_group("{}-{}".format(ConfigClass.AD_PROJECT_GROUP_PREFIX, code), user["name"], _logger)
        _logger.info('user email: {}'.format(user["email"]))


def create_folder_usernamespace(users, project_code):
    for user in users:
        try:
            _logger.info(f"creating namespace folder in greenroom and core for user : {user['name']}")
            zone_list = ["greenroom", "core"]
            for zone in zone_list:
                payload = {
                    "folder_name": user["name"],
                    "project_code": project_code,
                    "zone": zone,
                    "uploader": user["name"],
                    "tags": []
                }
                folder_creation_url = ConfigClass.DATA_UPLOAD_SERVICE_GREENROOM + '/folder'
                res = requests.post(
                    url=folder_creation_url,
                    json=payload
                )
                if res.status_code == 200:
                    _logger.info(
                        f"Namespace folder created successfully for user : {user['name']}")
        except Exception as error:
            _logger.error(
                f"Error while trying to create namespace folder for user : {user['name']} : {error}")


def bulk_create_folder_usernamespace(users, project_code):
    try:
        zone_list = ["greenroom", "core"]
        for zone in zone_list:
            folders = []
            for user in users:
                folders.append({
                    "name": user["name"],
                    "project_code": project_code,
                    "uploader": user["name"],
                    "tags": []
                })

            folder_creation_url = ConfigClass.DATA_UPLOAD_SERVICE_GREENROOM + '/folder/bulk'
            payload = {
                "folders": folders,
                "zone": zone,
            }
            res = requests.post(
                url=folder_creation_url,
                json=payload
            )
            if res.status_code == 200:
                _logger.info(
                    f"Namespace folders created successfully for users")

    except Exception as error:
        _logger.error(
            f"Error while trying to bulk create namespace folder, error: {error}")
