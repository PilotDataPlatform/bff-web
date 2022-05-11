from services.neo4j_service.neo4j_client import Neo4jClient
from models.api_response import APIResponse, EAPIResponseCode
from config import ConfigClass
from flask_jwt import current_identity


def check_dataset_permissions(dataset_geid):
    api_response = APIResponse()
    neo4j_client = Neo4jClient()
    response = neo4j_client.node_query("Dataset", {"global_entity_id": dataset_geid}) 
    if not response.get("result"):
        api_response.set_code(EAPIResponseCode.not_found)
        api_response.set_result("Dataset not found")
        return False, api_response
    dataset_node = response.get("result")[0]

    if dataset_node["creator"] != current_identity["username"]:
        api_response.set_code(EAPIResponseCode.forbidden)
        api_response.set_result("Permission Denied")
        return False, api_response
    return True, None


