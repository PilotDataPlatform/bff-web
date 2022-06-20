# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
