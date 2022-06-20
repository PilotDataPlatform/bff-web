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
# from ..upload_ops import CheckUploadStateRestful
from .vfolder_ops import VirtualFolderFiles, VirtualFolder, VirtualFolderInfo
from .file_ops import FileActions, FileActionTasks
from .file_search import FileSearch
from .meta import FileMeta, FileDetailBulk
from .file_stats import FileStatistics
from flask_restx import Resource, Namespace
from config import ConfigClass

nfs_entity_ns = Namespace('File Operation', description='Operation on files', path='/v1/files')

nfs_entity_ns.add_resource(FileActions, '/actions')
nfs_entity_ns.add_resource(FileActionTasks, '/actions/tasks')
nfs_entity_ns.add_resource(FileMeta, '/meta')
nfs_entity_ns.add_resource(FileDetailBulk, '/bulk/detail')
nfs_entity_ns.add_resource(FileStatistics, '/project/<project_geid>/files/statistics')


nfs_upload_ns = Namespace('Data Upload', description='Upload data', path='/v1/upload')

# downstream deprecated
# nfs_upload_ns.add_resource(CheckUploadStateRestful,
#                            '/containers/<container_id>/upload-state')

nfs_vfolder_ns = Namespace('Collections', description='APIs for collections (formerly virtualfolders)', path='/v1')
nfs_vfolder_ns.add_resource(VirtualFolderFiles, '/collections/<collection_geid>/files')
nfs_vfolder_ns.add_resource(VirtualFolder, '/collections')
nfs_vfolder_ns.add_resource(VirtualFolderInfo, '/collections/<collection_geid>')


nfs_entity_ns_v4 = Namespace('File ElasticSearch', description='File Search', path='/v1/<project_geid>/files')
nfs_entity_ns_v4.add_resource(FileSearch, '/search')
