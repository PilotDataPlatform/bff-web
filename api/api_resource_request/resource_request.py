from flask_restx import Resource
from flask_jwt import jwt_required, current_identity
from flask import request
import requests
from datetime import datetime
import math

from api import module_api
from models.api_response import APIResponse, EAPIResponseCode
from models.api_meta_class import MetaAPI
from models.api_resource_request import ResourceRequest, db
from config import ConfigClass
from services.notifier_services.email_service import SrvEmail
from common import LoggerFactory
from services.permissions_service.decorators import permissions_check
from resources.error_handler import APIException

api_resource = module_api.namespace('ResourceRequest', description='Resource Request API', path='/v1')

_logger = LoggerFactory('api_resource_request').get_logger()


class APIResourceRequest(metaclass=MetaAPI):
    def api_registry(self):
        api_resource.add_resource(self.ResourceRequestComplete, '/resource-request/<id>/complete')
        api_resource.add_resource(self.ResourceRequest, '/resource-request/<id>/')
        api_resource.add_resource(self.ResourceRequests, '/resource-requests')
        api_resource.add_resource(self.ResourceRequestsQuery, '/resource-requests/query')

    class ResourceRequest(Resource):
        @jwt_required()
        @permissions_check('resource_request', '*', 'view')
        def get(self, id):
            """
             Get a single resource request
            """
            api_response = APIResponse()
            _logger.info("ResourceRequest get called")

            if current_identity["role"] != "admin":
                api_response.set_error_msg("Permissions denied")
                api_response.set_code(EAPIResponseCode.forbidden)
                return api_response.to_dict, api_response.code

            try:
                resource_request = db.session.query(ResourceRequest).get(id)
                if not resource_request:
                    api_response.set_code(EAPIResponseCode.not_found)
                    api_response.set_result("Resource Request not found")
                    return api_response.to_dict, api_response.code
            except Exception as e:
                _logger.error("Psql Error: " + str(e))
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result("Psql Error: " + str(e))
                return api_response.to_dict, api_response.code
            api_response.set_result(resource_request.to_dict())
            return api_response.to_dict, api_response.code

        @jwt_required()
        @permissions_check('resource_request', '*', 'delete')
        def delete(self, id):
            api_response = APIResponse()
            _logger.info("ResourceRequest get called")

            try:
                resource_request = db.session.query(ResourceRequest).get(id)
                if not resource_request:
                    api_response.set_code(EAPIResponseCode.not_found)
                    api_response.set_result("Resource Request not found")
                db.session.delete(resource_request)
                db.session.commit()
            except Exception as e:
                _logger.error("Psql Error: " + str(e))
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result("Psql Error: " + str(e))
                return api_response.to_dict, api_response.code
            api_response.set_result('success')
            return api_response.to_dict, api_response.code

    class ResourceRequestComplete(Resource):
        @jwt_required()
        @permissions_check('resource_request', '*', 'update')
        def put(self, id):
            """
                Update an existing resource request as complete
            """
            api_response = APIResponse()
            _logger.info("ResourceRequestComplete put called")

            try:
                resource_request = db.session.query(ResourceRequest).get(id)
                if not resource_request:
                    api_response.set_code(EAPIResponseCode.not_found)
                    api_response.set_result("Resource Request not found")
                    return api_response.to_dict, api_response.code
                resource_request.active = False
                resource_request.complete_date = datetime.utcnow() 
                db.session.add(resource_request)
                db.session.commit()
                db.session.refresh(resource_request)
            except Exception as e:
                _logger.error("Psql Error: " + str(e))
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result("Psql Error: " + str(e))
                return api_response.to_dict, api_response.code

            try:
                # Get dataset
                payload = {"global_entity_id": resource_request.project_geid}
                response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/Container/query", json=payload)
                if not response.json():
                    api_response.set_code(EAPIResponseCode.forbidden)
                    api_response.set_result("Container not found in neo4j")
                    return api_response.to_dict, api_response.code
                dataset_node = response.json()[0]
            except Exception as e:
                _logger.error("Neo4j Error: " + str(e))
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result("Neo4j Error: " + str(e))
                return api_response.to_dict, api_response.code

            template_kwargs = {
                "current_user": current_identity["username"],
                "request_for": resource_request.request_for,
                "project_name": resource_request.project_name,
                "project_code": dataset_node["code"],
                "admin_email": ConfigClass.EMAIL_SUPPORT,
            }
            try:
                email_sender = SrvEmail()
                email_sender.send(
                    f"Access granted to {resource_request.request_for}",
                    [resource_request.email],
                    msg_type='html',
                    template="resource_request/approved.html",
                    template_kwargs=template_kwargs,
                )
                _logger.info(f"Email sent to {resource_request.email}")
            except Exception as e:
                _logger.error("Error sending email: " + str(e))
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result("Error sending email: " + str(e))
                return api_response.to_dict, api_response.code

            api_response.set_result(resource_request.to_dict())
            return api_response.to_dict, api_response.code

    class ResourceRequestsQuery(Resource):
        @jwt_required()
        def post(self):
            """
                List resource requests
            """
            _logger.info("ResourceRequestsQuery post called")
            api_response = APIResponse()
            data = request.get_json()

            page = int(data.get('page', 0))
            # use 0 start for consitency with other pagination systems
            page = page + 1
            page_size = int(data.get('page_size', 25))
            order_by = data.get('order_by', "request_date")
            order_type = data.get('order_type', "asc")
            filters = data.get('filters', {})

            try:
                query = None
                if current_identity["role"] != "admin":
                    filters["username"] = current_identity["username"]

                for key, value in filters.items():
                    query = db.session.query(ResourceRequest).filter(getattr(ResourceRequest, key).contains(value))
                if not query:
                    query = db.session.query(ResourceRequest)
                if order_by and order_type == "desc":
                    query = query.order_by(getattr(ResourceRequest, order_by).desc())
                else:
                    query = query.order_by(getattr(ResourceRequest, order_by).asc())
                resource_requests = query.paginate(page=page, per_page=page_size, error_out=False)
            except Exception as e:
                _logger.error("Psql error: " + str(e))
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result("Psql error: " + str(e))
                return api_response.to_dict, api_response.code

            total = resource_requests.total
            results = []
            for resource in resource_requests.items:
                results.append(resource.to_dict())
            api_response.set_page(page - 1)
            api_response.set_num_of_pages(math.ceil(total / page_size))
            api_response.set_total(total)
            api_response.set_result(results)
            return api_response.to_dict, api_response.code

    class ResourceRequests(Resource):

        @jwt_required()
        @permissions_check('resource_request', '*', 'create')
        def post(self):

            """
                Create a new resource request, send email notification
            """
            _logger.info("ResourceRequests post called")
            api_response = APIResponse()
            data = request.get_json()
            try:
                # validate payload
                is_valid, res, code = validate_payload(data)
                if not is_valid:
                    return res, code
                else:
                    model_data = res

                duplicate_check(data)

                # get user node
                user_node = get_user_node(data["user_id"])

                # get dataset
                is_dataset, dataset_res, code = get_dataset(data)
                if not is_dataset:
                    return dataset_res, code
                else:
                    dataset_node = dataset_res

                model_data["username"] = user_node["username"]
                model_data["email"] = user_node["email"]
                model_data["project_name"] = dataset_node["name"]

                user_role = None
                for role in get_realm_roles(user_node["username"]):
                    if role["name"].split("-")[0] == dataset_node["code"]:
                        user_role = role["name"].split("-")[-1]
                        break

                is_db, resource_request_res, code = db_resource_request(model_data)
                if not is_db:
                    return resource_request_res, code
                else:
                    resource_request = resource_request_res

                # send_email
                is_email_sent, email_res, code = send_email(resource_request, dataset_node, user_role)
                if not is_email_sent:
                    return email_res, code
                api_response.set_result(resource_request.to_dict())
                return api_response.to_dict, api_response.code

            except Exception as e:
                raise e
                _logger.error("Psql error: " + str(e))
                api_response.set_code(EAPIResponseCode.internal_error)
                api_response.set_result("Psql error: " + str(e))
                return api_response.to_dict, api_response.code


def validate_payload(data):
    api_response = APIResponse()
    model_data = {}
    required_fields = ["user_id", "project_geid", "request_for"]
    for field in required_fields:
        if field in data:
            model_data[field] = data[field]
            continue
        api_response.set_code(EAPIResponseCode.bad_request)
        api_response.set_result(f"Missing required field {field}")
        return False, api_response.to_dict, api_response.code
    if not data["request_for"] in ConfigClass.RESOURCES:
        api_response.set_code(EAPIResponseCode.bad_request)
        api_response.set_result("Invalid request_for field")
        return False, api_response.to_dict, api_response.code
    return True, model_data, 200


def duplicate_check(data):
    api_response = APIResponse()
    try:
        resource_requests = db.session.query(ResourceRequest).filter_by(
            user_id=data["user_id"],
            project_geid=data["project_geid"],
            request_for=data["request_for"],
        )
        if resource_requests.count() > 0:
            if resource_requests.first().active:
                error_msg = "Request already exists"
                raise APIException(status_code=EAPIResponseCode.conflict.value, error_msg=error_msg)
            else:
                error_msg = "Request already completed"
                raise APIException(status_code=EAPIResponseCode.conflict.value, error_msg=error_msg)
    except Exception as e:
        _logger.error("Psql error: " + str(e))
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg="Psql error:" + str(e))


def get_user_node(user_id: str) -> dict:
    api_response = APIResponse()
    payload = {
        "user_id": user_id,
    }
    response = requests.get(ConfigClass.AUTH_SERVICE + "admin/user", params=payload)
    if not response.json()["result"]:
        raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg="User not found in keycloak")
    user_node = response.json()["result"]

    if current_identity["username"] != user_node["username"]:
        raise APIException(status_code=EAPIRespnseCode.forbidden.value, error_msg="Permission Denied")
    return user_node


def get_realm_roles(username: str) -> list:
    payload = {
        "username": username,
    }
    response = requests.get(ConfigClass.AUTH_SERVICE + "admin/users/realm-roles", params=payload)
    if not response.json():
        raise APIException(status_code=EAPIRespnseCode.not_found.value, error_msg="User not found in keycloak")
    return response.json()["result"]


def get_dataset(data):
    api_response = APIResponse()
    payload = {"global_entity_id": data["project_geid"]}
    response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/Container/query", json=payload)
    if not response.json():
        api_response.set_code(EAPIResponseCode.forbidden)
        api_response.set_result("Container not found in neo4j")
        return False, api_response.to_dict, api_response.code
    dataset_node = response.json()[0]
    return True, dataset_node, 200


def db_resource_request(model_data):
    api_response = APIResponse()
    try:
        resource_request = ResourceRequest(**model_data)
        db.session.add(resource_request)
        db.session.commit()
        db.session.refresh(resource_request)
        return True, resource_request, 200
    except Exception as e:
        _logger.error("Psql error: " + str(e))
        api_response.set_code(EAPIResponseCode.internal_error)
        api_response.set_result("Psql Error: " + str(e))
        return False, api_response.to_dict, api_response.code


def send_email(resource_request, dataset_node, user_role):
    api_response = APIResponse()
    template_kwargs = {
        "username": resource_request.username,
        "request_for": resource_request.request_for,
        "project_name": resource_request.project_name,
        "project_code": dataset_node["code"],
        "admin_email": ConfigClass.EMAIL_SUPPORT,
        "portal_url": ConfigClass.SITE_DOMAIN,
        "user_role": user_role.title()
    }
    try:
        query = {"username": ConfigClass.RESOURCE_REQUEST_ADMIN}
        response = requests.get(ConfigClass.AUTH_SERVICE + "admin/user", params=query)
        admin_email = response.json()["result"]["email"]
    except Exception as e:
        _logger.error("Error getting admin email: " + str(e))
        api_response.set_code(EAPIResponseCode.internal_error)
        api_response.set_result("Error getting admin email: " + str(e))
        return False, api_response.to_dict, api_response.code

    try:
        email_sender = SrvEmail()
        email_sender.send(
            "Resource Request from " + template_kwargs["username"],
            [admin_email],
            msg_type='html',
            template="resource_request/request.html",
            template_kwargs=template_kwargs,
        )
        _logger.info(f"Email sent to {admin_email}")
        return True, None, 200
    except Exception as e:
        _logger.error("Error sending email: " + str(e))
        api_response.set_code(EAPIResponseCode.internal_error)
        api_response.set_result("Error sending email: " + str(e))
        return False, api_response.to_dict, api_response.code
