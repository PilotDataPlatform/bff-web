from .api_files.proxy import BaseProxyResource
from models.api_meta_class import MetaAPI
from config import ConfigClass
from api import module_api


api_ns_cataloguing = module_api.namespace(
    'Cataloguing Restful', description='Portal Cataloguing Restful', path='/v1')


# class APICataloguing(metaclass=MetaAPI):
#     def api_registry(self):
#         api_ns_cataloguing.add_resource(
#             self.DataLineage, '/lineage')

#     class DataLineage(BaseProxyResource):
#         url = ConfigClass.CATALOGUING_SERVICE + "lineage"
#         methods = ["GET"]
#         required_roles = {"GET": "member"}
