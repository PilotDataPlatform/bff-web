from api.module_api import module_api

datasets_entity_ns = module_api.namespace(
    'Portal Containers Actions', description='Operation on containers', path='/v1/containers')
users_entity_ns = module_api.namespace(
    'Portal User Actions', description='Operation on users', path='/v1/users')

entity_ns_v2 = module_api.namespace(
    'Portal Containers Actions V2', description='Operation on containers', path='/v2/containers')
