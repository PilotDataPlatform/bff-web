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
import asyncio
import re
from uuid import uuid4

import ldap
import ldap.modlist as modlist
import requests
from common import (LoggerFactory, ProjectClientSync, ProjectNotFoundException,
                    get_boto3_admin_client, get_minio_policy_client)
from flask import request
from flask_jwt import jwt_required
from flask_restx import Resource

from api import module_api
from config import ConfigClass
from models.api_meta_class import MetaAPI
from models.api_response import APIResponse, EAPIResponseCode
from resources.error_handler import APIException
from resources.minio import (get_admin_policy, get_collaborator_policy,
                             get_contributor_policy)
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

            if post_data.get("icon"):
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
        boto_client = asyncio.run(get_boto3_admin_client(
            ConfigClass.MINIO_ENDPOINT,
            ConfigClass.MINIO_ACCESS_KEY,
            ConfigClass.MINIO_SECRET_KEY
        ))
        prefixs = ["gr-", "core-"]
        for bucket_prefix in prefixs:
            bucket_name = bucket_prefix + project_code
            asyncio.run(boto_client.create_bucket(bucket_name))
            asyncio.run(boto_client.set_bucket_versioning(bucket_name))

            if ConfigClass.MINIO_BUCKET_ENCRYPTION:
                _logger.info('Bucket encyrption enabled, encrypting %s' % bucket_name)
                asyncio.run(boto_client.create_bucket_encryption(bucket_name))
            else:
                _logger.warn('Bucket encryption is not enabled, not encrypting %s' % bucket_name)

            mc = asyncio.run(get_minio_policy_client(
                ConfigClass.MINIO_ENDPOINT,
                ConfigClass.MINIO_ACCESS_KEY,
                ConfigClass.MINIO_SECRET_KEY,
                https=ConfigClass.MINIO_HTTPS
            ))

            # add MinIO policies for respective bucket (admin, collaborator, contributor)
            admin_policy_content = get_admin_policy(project_code)
            asyncio.run(mc.create_IAM_policy(str(uuid4()), admin_policy_content))
            contrib_policy_content = get_contributor_policy(project_code)
            asyncio.run(mc.create_IAM_policy(str(uuid4()), contrib_policy_content))
            collab_policy_content = get_collaborator_policy(project_code)
            asyncio.run(mc.create_IAM_policy(str(uuid4()), collab_policy_content))
            _logger.info(f"MinIO policies successfully applied for: {bucket_name}")
    except Exception as e:
        error_msg = f"Error when creating MinIO bucket and policies: {str(e)}"
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)


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
        zone_list = ["greenroom", "core"]
        folders = []
        for zone in zone_list:
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
