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
from enum import Enum

class EUserRole(Enum):
    site_admin = -1
    admin = 0
    collaborator = 1
    member = 2
    contributor = 3
    visitor = 4

def map_role_front_to_sys(role: str):
    '''
    return EUserRole Type
    '''
    return {
        'site-admin': EUserRole.site_admin,
        'admin': EUserRole.admin,
        'member': EUserRole.member,
        'contributor': EUserRole.contributor,
        'uploader': EUserRole.contributor,
        'visitor': EUserRole.visitor,
        'collaborator': EUserRole.collaborator
    }.get(role, None)

def map_role_sys_to_front(role: EUserRole):
    '''
    return string
    '''
    return {
        EUserRole.site_admin: 'site-admin',
        EUserRole.admin: 'admin',
        EUserRole.member: 'member',
        EUserRole.contributor: 'contributor',
        EUserRole.visitor: 'visitor',
        EUserRole.collaborator: 'collaborator'
    }.get(role, None)


def map_role_to_frontend(role: str):
    return {
        'site-admin': 'Platform Administrator', 
        'admin': 'Project Administrator', 
        'member': 'Member',
        'contributor': 'Project Contributor',
        'uploader': 'Project Contributor',
        'visitor': 'Visitor',
        'collaborator': 'Project Collaborator'
    }.get(role, 'Member')
