from flask_restx import Api
from api.api_files import nfs_entity_ns, nfs_upload_ns, nfs_vfolder_ns, nfs_entity_ns_v4
from resources.error_handler import APIException

module_api = Api(
    version='1.0',
    title='Portal API',
    description='BFF Portal API',
    doc='/v1/api-doc',
)


@module_api.errorhandler(APIException)
def http_exception_handler(exc: APIException):
    return exc.content, exc.status_code


# add the namespace for APIs (for new api development, please follow the latest convention.)
module_api.add_namespace(nfs_entity_ns)
module_api.add_namespace(nfs_upload_ns)
module_api.add_namespace(nfs_entity_ns_v4)
module_api.add_namespace(nfs_vfolder_ns)
