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
from flask_restx import Api
from api.api_files import nfs_entity_ns, nfs_upload_ns, nfs_vfolder_ns, nfs_entity_ns_v4
from resources.error_handler import APIException
from common import ProjectException

module_api = Api(
    version='1.0',
    title='Portal API',
    description='BFF Portal API',
    doc='/v1/api-doc',
)


@module_api.errorhandler(APIException)
def http_exception_handler(exc: APIException):
    return exc.content, exc.status_code


@module_api.errorhandler(ProjectException)
def project_exception_handler(exc: ProjectException):
    return exc.content, exc.status_code


# add the namespace for APIs (for new api development, please follow the latest convention.)
module_api.add_namespace(nfs_entity_ns)
module_api.add_namespace(nfs_upload_ns)
module_api.add_namespace(nfs_entity_ns_v4)
module_api.add_namespace(nfs_vfolder_ns)
