from flask import request
from config import ConfigClass
import requests
import json
import math
from datetime import timezone
import datetime
from models.api_response import APIResponse
from services.permissions_service.utils import has_permission


def check_invite_permissions(dataset_node, current_identity):
    if not dataset_node:
        # Only platform admin can invite without a project
        if current_identity["role"] != "admin":
            return False
    if current_identity["role"] != "admin":
        if not has_permission(dataset_node["code"], 'invite', '*', 'create'):
            return False
    return True


def remove_user_from_project_group(project_code, user_email, logger):
    # Remove user from keycloak group with the same name as the project
    payload = {
        "operation_type": "remove",
        "user_email": user_email,
        "group_code": project_code,
    }
    res = requests.put(
        url=ConfigClass.AUTH_SERVICE + "user/ad-group",
        json=payload,
    )
    if(res.status_code != 200):
        logger.error(
            f"Error removing user from group in ad: {res.text} {res.status_code}")


def add_user_to_ad_group(user_email, project_code, logger):
    payload = {
        "operation_type": "add",
        "user_email": user_email,
        "group_code": project_code,
    }
    res = requests.put(
        url=ConfigClass.AUTH_SERVICE + "user/ad-group",
        json=payload,
    )
    if(res.status_code != 200):
        logger.error(f"Error adding user to group in ad: {res.text} {res.status_code}")

    return res.json().get("entry")


######################################################### DATASET API #################################################

def retreive_property(token, label):
    url = ConfigClass.NEO4J_SERVICE + "nodes/%s/properties" % label
    headers = {
        'Authorization': token
    }
    res = requests.get(
        url=url,
        headers=headers,
    )
    return json.loads(res.text)

# TODO the neo4j dont need the token
def check_container_exist(label, container_id):
    url = ConfigClass.NEO4J_SERVICE + "nodes/%s/node/" % label + container_id
    res = requests.get(url=url)
    return json.loads(res.text)


def neo4j_query_with_pagination(url, data, partial=False):
    page = int(data.get('page', 0))
    if data.get("page_size"):
        page_size = int(data.get('page_size', 25))
    else:
        page_size = None
    data = data.copy()
    if "page" in data:
        del data["page"]
    if "page_size" in data:
        del data["page_size"]

    # Get token from reuqest's header
    access_token = request.headers.get("Authorization", None)
    page_data = {
        "partial": partial,
        **data
    }
    if page_size:
        page_data["limit"] = page_size
    if page and page_size:
        page_data["skip"] = page * page_size
    headers = {
        'Authorization': access_token
    }
    # Request to get page results
    res = requests.post(
        url=url,
        headers=headers,
        json=page_data,
    )
    if page_data.get("limit"):
        del page_data["limit"]
    if page_data.get("skip"):
        del page_data["skip"]
    if "order_by" in page_data:
        del page_data["order_by"]
    if "order_type" in page_data:
        del page_data["order_type"]

    # Get page count
    count_res = requests.post(
        url=url + "/count",
        headers=headers,
        json={"count": True, **page_data},
    )
    res_data = json.loads(count_res.content)
    total = res_data.get('count')
    response = APIResponse()
    response.set_result(json.loads(res.content))
    response.set_page(page)
    response.set_total(total)
    if page_size:
        num_of_pages = math.ceil(total / page_size)
    else:
        num_of_pages = 1
    response.set_num_of_pages(num_of_pages)
    return response

################################################### Simple Helpers ########################################

def helper_now_utc():
    dt = datetime.datetime.now()
    utc_time = dt.replace(tzinfo=timezone.utc)
    return utc_time


def http_query_node(primary_label, query_params={}):
    '''
    primary_label i.e. Folder, File, Container
    '''
    payload = {
        **query_params
    }
    node_query_url = ConfigClass.NEO4J_SERVICE + \
        "nodes/{}/query".format(primary_label)
    response = requests.post(node_query_url, json=payload)
    return response


def get_files_recursive(folder_geid, all_files=[]):
    query = {
        "start_label": "Folder",
        "end_labels": ["File", "Folder"],
        "query": {
            "start_params": {
                "global_entity_id": folder_geid,
            },
            "end_params": {
            }
        }
    }
    resp = requests.post(ConfigClass.NEO4J_SERVICE_V2 +
                         "relations/query", json=query)
    for node in resp.json()["results"]:
        if "File" in node["labels"]:
            all_files.append(node)
        else:
            get_files_recursive(node["global_entity_id"], all_files=all_files)
    return all_files


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
