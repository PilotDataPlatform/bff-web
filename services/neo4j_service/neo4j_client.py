import requests
from config import ConfigClass


def catch_internal(func):
    '''
    decorator to catch internal server error.
    '''
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return {
                "error_msg": str(e),
                "result": "",
                "code": 500,
            }
    return inner


class Neo4jClient(object):

    def __init__(self):
        self.result = {
            "result": None,
            "error_msg": "",
            "code": 200,
        }

    # Shared
    @catch_internal
    def node_get(self, label, id):
        response = requests.get(
            ConfigClass.NEO4J_SERVICE + f"nodes/{label}/node/{id}")
        result = self.result.copy()
        if not response.json():
            result["error_msg"] = "Node not found"
            result["code"] = 404
            return result
        result["result"] = response.json()[0]
        return result

    @catch_internal
    def node_create(self, label, data):
        response = requests.post(
            ConfigClass.NEO4J_SERVICE + f"nodes/{label}", json=data)
        result = self.result.copy()
        result["result"] = response.json()
        return result

    @catch_internal
    def node_query(self, label, data):
        response = requests.post(
            ConfigClass.NEO4J_SERVICE + f"nodes/{label}/query", json=data)
        result = self.result.copy()
        result["result"] = response.json()
        return result

    @catch_internal
    def get_relation(self, start_id, end_id):
        relation_query = {"start_id": start_id, "end_id": end_id}
        response = requests.get(
            ConfigClass.NEO4J_SERVICE + f"relations", params=relation_query)
        result = self.result.copy()
        result["result"] = response.json()
        return result

    @catch_internal
    def create_relation(self, start_id, end_id, label, properties={}):
        payload = {"start_id": start_id, "end_id": end_id}
        if properties:
            payload['properties'] = properties
        response = requests.post(
            ConfigClass.NEO4J_SERVICE + f"relations/{label}", json=payload)
        result = self.result.copy()
        result["result"] = response.json()
        return result

    @catch_internal
    def update_node(self, label, node_id, data):
        response = requests.put(
            ConfigClass.NEO4J_SERVICE + f"nodes/{label}/node/{node_id}", json=data)
        result = self.result.copy()
        result["result"] = response.json()
        return result

    # Containers

    def get_container_by_geid(self, geid):
        response = self.node_query("Container", {"global_entity_id": geid})
        if not response.get("result"):
            if not response.get("error_msg"):
                self.result["error_msg"] = "Container not found"
                self.result["code"] = 404
            return self.result
        dataset_node = response["result"][0]
        self.result["result"] = response["result"][0]
        return self.result

    def get_container_by_code(self, code):
        response = self.node_query("Container", {"code": code})
        if not response.get("result"):
            if not response.get("error_msg"):
                response["error_msg"] = "Container not found"
                response["code"] = 404
            return response
        dataset_node = response["result"][0]
        response["result"] = dataset_node
        return response

    def get_project_linked_folders(self, project_code):
        url = ConfigClass.NEO4J_SERVICE + "relations/query"
        payload = {
            "start_label": "Container",
            "end_label": "Folder",
            "start_params": {"code": project_code}
        }
        response = requests.post(
            url=url,
            json=payload
        )
        return response.json()
