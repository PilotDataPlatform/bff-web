from models.api_meta_class import MetaAPI

from .api_aduser_update import ADUserUpdate
from .api_container_user import ContainerUser
from .api_containers import Container, Containers
from .api_folder_creation import FolderCreation
from .namespace import datasets_entity_ns, users_entity_ns
from .user_operation import (ContainerAdmins, ContainerUsers,
                             UserContainerQuery, Users)


class APIContainer(metaclass=MetaAPI):
    def api_registry(self):
        datasets_entity_ns.add_resource(Containers, '/')

        # Actions on specific dataset
        datasets_entity_ns.add_resource(Container, '/<project_id>')

        # Actions on multiple users
        datasets_entity_ns.add_resource(ContainerUsers, '/<project_id>/users')
        datasets_entity_ns.add_resource(ContainerAdmins, '/<project_id>/admins')

        # add the folder operation
        datasets_entity_ns.add_resource(FolderCreation, '/<project_id>/folder')

        # Actions on the specific user

        datasets_entity_ns.add_resource(ContainerUser, '/<project_id>/users/<username>')
        # Actions on users
        users_entity_ns.add_resource(Users, '/platform')
        users_entity_ns.add_resource(UserContainerQuery, '/<username>/containers')
        users_entity_ns.add_resource(ADUserUpdate, '')
