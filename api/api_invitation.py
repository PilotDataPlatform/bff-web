from flask_restx import Api, Resource, fields
from flask_jwt import jwt_required, current_identity
from config import ConfigClass
from models.api_response import APIResponse, EAPIResponseCode
from models.api_meta_class import MetaAPI
from models.invitation import db, InvitationModel, InvitationForm
from resources.swagger_modules import create_invitation_request_model, create_invitation_return_example
from resources.swagger_modules import read_invitation_return_example
from resources.utils import check_invite_permissions, fetch_geid, get_container_id
from resources.validations import boolean_validate_role
from resources.utils import add_user_to_ad_group
from services.invitation_services.invitation_manager import SrvInvitationManager
from services.logger_services.logger_factory_service import SrvLoggerFactory
from services.neo4j_service.neo4j_client import Neo4jClient
from services.permissions_service.utils import has_permission
from services.neo4j_service.neo4j_client import Neo4jClient
from multiprocessing import Process
from api import module_api
from flask import request
import json
import requests
import math
import ldap
import datetime
import ldap
import ldap.modlist as modlist

api_ns_invitations = module_api.namespace(
    'Invitation Restful', description='Portal Invitation Restful', path='/v1')
api_ns_invitation = module_api.namespace(
    'Invitation Restful', description='Portal Invitation Restful', path='/v1')


class APIInvitation(metaclass=MetaAPI):
    def api_registry(self):
        api_ns_invitations.add_resource(
            self.InvitationsRestful, '/invitations')
        api_ns_invitation.add_resource(
            self.CheckUserPlatformRole, '/invitation/check/<email>')
        api_ns_invitation.add_resource(
            self.PendingUserRestful, '/invitation-list')

    class InvitationsRestful(Resource):
        @api_ns_invitations.expect(create_invitation_request_model)
        @api_ns_invitations.response(200, create_invitation_return_example)
        @jwt_required()
        def post(self):
            '''
            This method allow to create invitation in platform.
            '''
            _logger = SrvLoggerFactory('api_invitation').get_logger()
            my_res = APIResponse()
            access_token = request.headers.get("Authorization", None)
            post_json = request.get_json()
            neo4j_client = Neo4jClient()

            _logger.info("Start Creating Invitation: {}".format(post_json))
            required_fields = ["email", "platform_role", "ad_account_created"]
            for field in required_fields:
                if not field in post_json:
                    my_res.set_result(f'missing required field {field}')
                    my_res.set_code(EAPIResponseCode.bad_request)
                    return my_res.to_dict, my_res.code

            email = post_json["email"]
            ad_account_created = post_json["ad_account_created"]
            ad_user_dn = post_json.get("ad_user_dn", None)
            relation_data = post_json.get("relationship")
            dataset_node = None
            invite_data = {
                "email": email,
                "platform_role": post_json["platform_role"],
            }
            if relation_data:
                required_fields = ["project_geid", "project_role", "inviter"]
                for field in required_fields:
                    if not relation_data.get(field):
                        my_res.set_result(
                            f'missing required relation field {field}')
                        my_res.set_code(EAPIResponseCode.bad_request)
                        return my_res.to_dict, my_res.code
                response = neo4j_client.get_container_by_geid(
                    relation_data.get("project_geid"))
                if response.get("code") != 200:
                    return response, response.get("code")
                dataset_node = response["result"]
                invite_data["projectId"] = dataset_node["id"]
                invite_data["project_role"] = relation_data["project_role"]
                invite_data["inviter"] = relation_data["inviter"]
            invitation_form = InvitationForm(invite_data)

            # Make sure the user doesn't already exist
            response = neo4j_client.get_user_by_email(email)
            if response.get("code") != 404:
                _logger.info('User already exists in platform')
                my_res.set_result('[ERROR] User already exists in platform')
                my_res.set_code(EAPIResponseCode.bad_request)
                return my_res.to_dict, my_res.code

            if not check_invite_permissions(dataset_node, current_identity):
                my_res.set_result('Permission denied')
                my_res.set_code(EAPIResponseCode.forbidden)
                return my_res.to_dict, my_res.code

            # Create user in neo4j
            response = neo4j_client.create_user({
                "email": email,
                "role": post_json["platform_role"],
                "status": post_json.get("status", "pending"),
                "global_entity_id": fetch_geid("User"),
            })
            if response.get("code") != 200:
                my_res.set_result(
                    'Error creating user in neo4j' + str(response.get("result")))
                my_res.set_code(EAPIResponseCode.internal_error)
                return my_res.to_dict, my_res.code
            user_node = response["result"]

            # Create relation in neo4j
            properties = {
                "status": "active"
            }
            if relation_data:
                response = neo4j_client.create_relation(
                    user_node["id"],
                    dataset_node["id"],
                    relation_data["project_role"],
                    properties=properties
                )
                if response.get("code") != 200:
                    my_res.set_result(
                        'Error creating relation in neo4j' + str(response.get("result")))
                    my_res.set_code(EAPIResponseCode.internal_error)
                    return my_res.to_dict, my_res.code

            ad_first = ""
            if ad_account_created:
                # Create Project User Group in ldap
                if not ad_user_dn:
                    my_res.set_result('[ERROR] Need user dn')
                    my_res.set_code(EAPIResponseCode.bad_request)
                    return my_res.to_dict, my_res.code

                conn = ldap.initialize(ConfigClass.LDAP_URL)
                conn.simple_bind_s(ConfigClass.LDAP_ADMIN_DN,
                                   ConfigClass.LDAP_ADMIN_SECRET)

                # Get user from ldap
                email = user_node["email"]
                user_query = f'(&(objectClass=user)(mail={email}))'
                res = conn.search_s(
                    ad_user_dn,
                    ldap.SCOPE_SUBTREE,
                    user_query,
                )
                user_dn, entry = res[0]

                ad_first = ""
                try:
                    ad_first = entry["givenName"][0].decode()
                except Exception as e:
                    # Failed to get first_name fall back to username
                    ad_first = entry["sAMAccountName"][0].decode()

                # add user to ad users group in ldap
                add_user_to_ad_group(email, ConfigClass.AD_USER_GROUP, _logger, access_token)

                if user_node["role"] == "admin":
                    # Add platform admin to all groups
                    response = requests.post(
                        ConfigClass.NEO4J_SERVICE + "nodes/Container/query", json={})
                    print(response.json())
                    if response.status_code != 200:
                        my_res.set_result(
                            "Error fetching projects: " + str(response.text))
                        my_res.set_code(EAPIResponseCode.internal_error)
                        return my_res.to_dict, my_res.code
                    project_codes = [i["code"] for i in response.json()]
                    add_entries = []
                    for code in project_codes:
                        p = Process(target=add_user_to_ad_group, args=(
                            email, code, _logger, access_token))
                        p.daemon = True
                        p.start()
                elif relation_data:
                    code = dataset_node["code"]
                    add_user_to_ad_group(email, code, _logger, access_token)
                conn.unbind_s()

                # Sync group info to keycloak

            # init invitation managemer
            invitation_mgr = SrvInvitationManager()
            invitation_mgr.save_invitation(
                invitation_form,
                access_token,
                current_identity,
                ad_account_created=ad_account_created,
                ad_first=ad_first,
            )

            my_res.set_result('[SUCCEED] Invitation Saved, Email Sent')
            _logger.info('Invitation Saved, Email Sent')
            my_res.set_code(EAPIResponseCode.success)
            return my_res.to_dict, my_res.code

    class CheckUserPlatformRole(Resource):
        @jwt_required()
        def get(self, email):
            '''
            This method allow to get user's detail on the platform.
            '''
            my_res = APIResponse()
            _logger = SrvLoggerFactory('api_invitation').get_logger()
            project_geid = request.args.get("project_geid")

            if current_identity["role"] != "admin" and not project_geid:
                my_res.set_result("Permission denied")
                my_res.set_code(EAPIResponseCode.unauthorized)
                return my_res.to_dict, my_res.code

            neo4j_client = Neo4jClient()
            response = neo4j_client.get_user_by_email(email)

            # Check if user exists in ad
            ad_account_created = False
            ad_user_dn = None
            ldap.set_option(ldap.OPT_REFERRALS, ldap.OPT_OFF)
            conn = ldap.initialize(ConfigClass.LDAP_URL)
            conn.simple_bind_s(ConfigClass.LDAP_ADMIN_DN,
                               ConfigClass.LDAP_ADMIN_SECRET)
            user_query = f'(&(objectClass=user)(mail={email}))'

            users = conn.search_s(
                "dc={},dc={}".format(ConfigClass.LDAP_DC1,
                                     ConfigClass.LDAP_DC2),
                ldap.SCOPE_SUBTREE,
                user_query
            )

            for user_dn, entry in users:
                if 'mail' in entry:
                    if entry['mail'][0].decode("utf-8") == email:
                        ad_account_created = True
                        ad_user_dn = user_dn
                        break

            if response.get("code") == 404:
                my_res.set_result({'msg': 'User does not exist in platform',
                                  'ad_account_created': ad_account_created, 'ad_user_dn': ad_user_dn})
                my_res.set_code(EAPIResponseCode.not_found)
                return my_res.to_dict, my_res.code
            elif response.get("code") != 200:
                return response
            user_node = response["result"]
            result = user_node
            result["relationship"] = {}
            result["ad_account_created"] = ad_account_created
            result["ad_user_dn"] = ad_user_dn

            if project_geid:
                response = neo4j_client.get_container_by_geid(project_geid)
                if response.get("code") == 404:
                    my_res.set_result('Container does not exist in platform')
                    my_res.set_code(EAPIResponseCode.not_found)
                    return my_res.to_dict, my_res.code
                elif response.get("code") != 200:
                    return response
                dataset_node = response["result"]

                if not has_permission(dataset_node["code"], 'invite', '*', 'create'):
                    my_res.set_result("Permission denied")
                    my_res.set_code(EAPIResponseCode.unauthorized)
                    return my_res.to_dict, my_res.code
                response = neo4j_client.get_relation(
                    user_node["id"], dataset_node["id"])
                if response.get("code") == 200 and response["result"]:
                    result["relationship"] = {
                        "project_code": dataset_node["code"],
                        "project_role": response["result"][0]["r"]["type"],
                        "project_geid": dataset_node["global_entity_id"],
                    }
                elif response.get("code") == 404:
                    pass
                elif response.get("code") == 200 and not response["result"]:
                    pass
                else:
                    my_res.set_result(response)
                    my_res.set_error_msg('Getting relation internal error')
                    my_res.set_code(EAPIResponseCode.internal_error)
                    return my_res.to_dict, my_res.code
            my_res.set_result(result)
            my_res.set_code(EAPIResponseCode.success)
            return my_res.to_dict, my_res.code

    class PendingUserRestful(Resource):
        @jwt_required()
        def post(self):
            '''
            This method allow to get all pending users from invitation links.
            '''
            # init logger
            _logger = SrvLoggerFactory('api_pending_users').get_logger()
            _logger.info('fetching pending user api triggered')
            # init resp
            my_res = APIResponse()

            try:
                # init invitation managemer
                invitation_mgr = SrvInvitationManager()

                post_json = request.get_json()

                page = post_json.get('page', 0)
                page_size = post_json.get('page_size', 25)
                order_by = post_json.get('order_by', None)
                order_type = post_json.get('order_type', None)

                filters = post_json.get('filters', None)
                project_geid = filters.get("project_id", None)

                # is filters has project_id, query project's invitations
                if project_geid:
                    query_params = {"global_entity_id": project_geid}
                    container_id = get_container_id(query_params)
                    filters['project_id'] = container_id
                    _logger.info('container_id: {}'.format(container_id))

                if current_identity["role"] != "admin":
                    client = Neo4jClient()
                    result = client.node_get("Container", container_id)
                    if result.get("code") != 200:
                        error_msg = result.get("error_msg")
                        _logger.error(
                            f"Couldn't get project for invite permissions check - {error_msg}")
                        my_res.set_code(EAPIResponseCode.forbidden)
                        my_res.set_error_msg('Permission denied')
                        return my_res.to_dict, my_res.code
                    project = result.get("result")
                    _logger.info('project["code"]: {}'.format(project["code"]))
                    if not has_permission(project["code"], 'invite', '*', 'view'):
                        my_res.set_code(EAPIResponseCode.forbidden)
                        my_res.set_error_msg('Permission denied')
                        return my_res.to_dict, my_res.code

                records, count = invitation_mgr.get_invitations(
                    page, page_size, filters, order_by, order_type)
                result = []
                _logger.info('records: {}'.format(records))
                for record in records:
                    detail = json.loads(record.invitation_detail)
                    user_info = {
                        'create_timestamp': record.create_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        'invited_by': record.invited_by,
                        'status': record.status,
                        **detail
                    }
                    result.append(user_info)
                my_res.set_result(result)
                my_res.set_total(count)
                my_res.set_num_of_pages(math.ceil(count/page_size))
                my_res.set_page(page)

                return my_res.to_dict, my_res.code
            except Exception as e:
                _logger.error('error in pending users' + str(e))
                my_res.set_code(EAPIResponseCode.internal_error)
                my_res.set_error_msg('Internal Error' + str(e))
                return my_res.to_dict, my_res.code
