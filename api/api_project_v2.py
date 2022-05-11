import json
import os
import re

import ldap
import ldap.modlist as modlist
import requests
from common import GEIDClient
from flask import request
from flask_jwt import jwt_required
from flask_restx import Resource
from common import LoggerFactory
from minio.sseconfig import Rule, SSEConfig
from minio.versioningconfig import ENABLED, VersioningConfig

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
from models.api_response import APIResponse, EAPIResponseCode
from resources.minio import (Minio_Client, create_admin_policy,
                             create_collaborator_policy,
                             create_contributor_policy)
from services.permissions_service.decorators import permissions_check

api_ns_projects = module_api.namespace('Project Restful', description='For project feature', path='/v1')

_logger = LoggerFactory('api_project').get_logger()


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

            description = post_data.get("description", None)
            dataset_code = post_data.get("code", None)

            try:
                # validate the payload and check if project exist
                is_valid, message = validate_post_data(post_data)
                if not is_valid:
                    _logger.error("Invalid post data")
                    _res.set_code(EAPIResponseCode.bad_request)
                    _res.set_error_msg(message["result"])
                    return _res.to_dict, _res.code

                is_dataset, res_datasets, _ = duplicate_check(dataset_code)
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
                _ = create_container_node(post_data)

                # Create MinIO bucket for project with name based on zone and dataset_code
                create_minio_bucket(dataset_code)

                # LDAP Operation
                # Create Project User Group in ldap
                ldap_create_user_group(dataset_code, description)

                # Keycloak Operation
                keycloak_create_roles(dataset_code)

                # because the platform admin is inside `platform-admin` role
                # so we dont do anything
                # create username namespace folder for all platform admin
                origin_users = get_platform_admins(dataset_code)
                bulk_create_folder_usernamespace(users=origin_users, project_code=dataset_code)

            except Exception as e:
                _logger.error('Error in creating project: {}'.format(str(e)))
                _res.set_code(EAPIResponseCode.forbidden)
                _res.set_error_msg('Error %s' % str(e))
                return _res.to_dict, _res.code

            # _res.set_result(container_result.json())
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
    post_data["global_entity_id"] = GEIDClient().get_GEID()

    res = requests.post(
        ConfigClass.NEO4J_SERVICE + "nodes/Container",
        json=post_data
    )
    if res.status_code != 200:
        raise Exception("Fail to create project node in neo4j "+str(res.__dict__))

    return res


def create_minio_bucket(project_code: str) -> None:
    try:
        prefixs = ["gr-", "core-"]
        for bucket_prefix in prefixs:

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
            os.popen('mc admin policy add minio %s %s' % (project_code + "-admin", policy_name))
            policy_name = create_contributor_policy(project_code)
            os.popen('mc admin policy add minio %s %s' % (project_code + "-contributor", policy_name))
            policy_name = create_collaborator_policy(project_code)
            os.popen('mc admin policy add minio %s %s' % (project_code + "-collaborator", policy_name))
            _logger.info(f"MinIO policies successfully applied for: {bucket_name}")

    except Exception as e:
        error_msg = f"Error when creating MinIO bucket: {str(e)}"
        _logger.error(error_msg)
        raise Exception(error_msg)

    return None


def ldap_create_user_group(code, description):
    try:
        ldap.set_option(ldap.OPT_REFERRALS, ldap.OPT_OFF)
        conn = ldap.initialize(ConfigClass.LDAP_URL)
        conn.simple_bind_s(ConfigClass.LDAP_ADMIN_DN,
                           ConfigClass.LDAP_ADMIN_SECRET)

        dn = "cn={}-{},ou=Gruppen,ou={},dc={},dc={}".format(
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


def get_platform_admins(code):
    payload = {
        "role_names": ["platform-admin"],
        "status": "active",
        "page_size": 1000,  # temperally here to get all undeer platform admin
    }
    response = requests.post(ConfigClass.AUTH_SERVICE + "admin/roles/users", json=payload)

    # exclude the admin user
    origin_users = response.json().get("result", [])

    return origin_users


def keycloak_create_roles(code: str):
    payload = {
        "realm": ConfigClass.KEYCLOAK_REALM,
        "project_roles": ["admin", "collaborator", "contributor"],
        "project_code": code
    }
    keycloak_roles_url = ConfigClass.AUTH_SERVICE + 'admin/users/realm-roles'
    res = requests.post(url=keycloak_roles_url, json=payload)
    if res.status_code != 200:
        error_msg = 'create realm role: ' + str(res.__dict__)
        _logger.error(error_msg)
        raise Exception(error_msg)

    return res


def bulk_create_folder_usernamespace(users: list, project_code: str):
    try:
        zone_list = [ConfigClass.GREENROOM_ZONE_LABEL, ConfigClass.CORE_ZONE_LABEL]
        for zone in zone_list:
            folders = []
            for user in users:
                folders.append({
                    "name": user["name"],
                    "zone": 0 if zone == "greenroom" else 1,
                    "type": "name_folder",
                    "owner": user["name"],
                    "container_code": project_code,
                    "container_type": "project",
                    "size": 0,
                    "location_uri": "",
                    "version": "",
                })

        res = requests.post(ConfigClass.METADATA_SERVICE + 'items/batch/', json={"items": folders})
        if res.status_code != 200:
            raise Exception(str(res.__dict__))

    except Exception as e:
        _logger.error(
            f"Error while trying to bulk create namespace folder, error: {e}")
        raise e
