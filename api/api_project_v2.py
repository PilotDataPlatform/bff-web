import os
import re

import ldap
import ldap.modlist as modlist
import requests
from common import ProjectClientSync, ProjectNotFoundException
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
from resources.error_handler import APIException

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
        @jwt_required()
        @permissions_check('project', '*', 'create')
        def post(self):
            """
            This method allow to create a new project in platform.
            Notice that top-level container could only be created by site admin.
            """
            post_data = request.get_json()
            _res = APIResponse()
            _logger.info('Calling API for creating project: {}'.format(post_data))

            description = post_data.get("description", None)
            project_code = post_data.get("code", None)

            validate_post_data(post_data)
            duplicate_check(project_code)

            payload = {
                "name": post_data.get("name"),
                "code": post_data.get("code"),
                "description": post_data.get("description"),
                "is_discoverable": post_data.get("discoverable"),
                "tags": post_data.get("tags"),
            }
            project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
            project = project_client.create(**payload)

            if "icon" in post_data:
                project.upload_logo(post_data["icon"])

            # Create MinIO bucket for project with name based on zone and dataset_code
            create_minio_bucket(project_code)

            # LDAP Operation
            # Create Project User Group in ldap
            ldap_create_user_group(project_code, description)

            # Keycloak Operation
            keycloak_create_roles(project_code)

            # because the platform admin is inside `platform-admin` role
            # so we dont do anything
            # create username namespace folder for all platform admin
            origin_users = get_platform_admins(project_code)
            bulk_create_folder_usernamespace(users=origin_users, project_code=project_code)

            return _res.to_dict, _res.code


def duplicate_check(project_code: str) -> bool:
    project_client = ProjectClientSync(ConfigClass.PROJECT_SERVICE, ConfigClass.REDIS_URL)
    try:
        project_client.get(code=project_code)
    except ProjectNotFoundException:
        return False
    raise APIException(
        error_msg="Error duplicate project code",
        status_code=EAPIResponseCode.conflict.value
    )


def validate_post_data(post_data: dict):
    name = post_data.get("name", None)
    code = post_data.get("code", None)

    if not name or not code:
        _logger.error('Field name and code field is required.')
        raise APIException(
            error_msg="Field name and code field is required.",
            status_code=EAPIResponseCode.bad_request.value
        )

    project_code_pattern = re.compile(ConfigClass.PROJECT_CODE_REGEX)
    is_match = re.search(project_code_pattern, code)

    if not is_match:
        _logger.error('Project code does not match the pattern.')
        raise APIException(
            status_code=EAPIResponseCode.bad_request.value,
            error_msg="Project code does not match the pattern."
        )

    project_name_pattern = re.compile(ConfigClass.PROJECT_NAME_REGEX)
    is_match = re.search(project_name_pattern, name)

    if not is_match:
        _logger.error('Project name does not match the pattern.')
        raise APIException(
            status_code=EAPIResponseCode.bad_request.value,
            error_msg="Project name does not match the pattern."
        )

    if post_data.get("icon"):
        # check if icon is bigger then limit
        if len(post_data.get("icon")) > ConfigClass.ICON_SIZE_LIMIT:
            raise APIException(
                status_code=EAPIResponseCode.bad_request.value,
                error_msg="icon too large"
            )


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
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
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
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
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
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=res.json())

    except Exception as e:
        error_msg = f"Error while trying to bulk create namespace folder, error: {e}"
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
