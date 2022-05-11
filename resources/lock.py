import httpx

from config import ConfigClass


def data_ops_request(resource_key: str, operation: str, method: str) -> dict:
    url = ConfigClass.DATA_UTILITY_SERVICE_v2 + 'resource/lock/'
    post_json = {'resource_key': resource_key, 'operation': operation}
    with httpx.Client() as client:
        response = client.request(url=url, method=method, json=post_json)
    if response.status_code != 200:
        raise Exception('resource %s already in used' % resource_key)

    return response.json()


def lock_resource(resource_key: str, operation: str) -> dict:
    return data_ops_request(resource_key, operation, 'POST')


def unlock_resource(resource_key: str, operation: str) -> dict:
    return data_ops_request(resource_key, operation, 'DELETE')
