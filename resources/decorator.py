from flask_jwt import current_identity
import requests
from config import ConfigClass
from functools import wraps
import json
from flask import request
from models.user_type import EUserRole, map_role_front_to_sys, map_role_neo4j_to_sys
from services.user_services.user_authorization import user_accessible


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
    return container_id


def check_role(required_role, parent=None):
    def inner_function(function):
        required_role_mapped = map_role_front_to_sys(required_role)

        @wraps(function)
        def wrapper(*args, **kwargs):
            user_id = current_identity["user_id"]
            role = current_identity["role"]
            role_mapped = map_role_front_to_sys(role)
            #########################################
            # note here this admin is platform wise #
            # and require_role is project wise      #
            #########################################
            # check if user is platform admin
            if(role_mapped == EUserRole.admin):
                res = function(*args, **kwargs)
                return res

            # required role is site admin
            if required_role_mapped == EUserRole.site_admin:
                return {'result': 'Permission Denied'}, 401

            dataset_id = None
            if 'project_geid' in kwargs:
                payload = {"global_entity_id": kwargs["project_geid"]}
                dataset_id = get_container_id(payload)
            elif 'dataset_id' in kwargs:
                dataset_id = kwargs['dataset_id']
            elif (parent):
                dataset_id = kwargs['dataset_id']

            # check if the relation is existed in neo4j
            try:
                url = ConfigClass.NEO4J_SERVICE + "relations"
                url += "?start_id=%d" % int(user_id)
                url += "&end_id=%d" % int(dataset_id)
                res = requests.get(url=url)
                if(res.status_code != 200):
                    raise Exception("Unauthorized: " +
                                    json.loads(res.text))
                relations = json.loads(res.text)

                if(len(relations) == 0):
                    raise Exception(
                        "Unauthorized: Relation does not exist.")
                if relations[0]["r"].get("status") in ["disable", "hibernate"]:
                    raise Exception(
                        "Unauthorized: Relation disabled")
            except Exception as e:
                return {'result': 'Permission Denied'}, 401

            for item in relations:
                project_role = item["r"]["type"]
                role_neo4j_mapped = map_role_neo4j_to_sys(project_role)
                current_identity['project_role'] = project_role
                if(user_accessible(required_role_mapped, role_neo4j_mapped)):
                    # if user accessible pass authorization and continue function
                    res = function(*args, **kwargs)
                    return res

            # if not pass the authorization
            return {'result': 'Permission Denied'}, 401
        return wrapper
    return inner_function


def check_user():
    def inner_function(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            current_user = current_identity["username"]
            role = current_identity["role"]
            
            username = kwargs['username']

            if current_user != username and role != 'admin':
                return {'result': 'Permission Denied'}, 401

            res = function(*args, **kwargs)
            return res

        return wrapper
    return inner_function
