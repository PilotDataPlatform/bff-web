# from ..upload_ops import CheckUploadStateRestful
from .vfolder_ops import VirtualFolderFiles, VirtualFolder, VirtualFolderInfo
from .file_ops import FileActions, FileActionTasks, FileValidation, FileRepeatedCheck
from .file_search import FileSearch
from .meta import FileMeta, FileMetaHome, FileDetailBulk, FileMetaV2, FileDetailBulkV2
from .file_stats import FileStatistics
from flask_restx import Resource, Namespace
from config import ConfigClass

nfs_entity_ns = Namespace('File Operation', description='Operation on files', path='/v1/files')

nfs_entity_ns.add_resource(FileActions, '/actions')
nfs_entity_ns.add_resource(FileActionTasks, '/actions/tasks')
nfs_entity_ns.add_resource(FileMetaHome, '/entity/meta/')
nfs_entity_ns.add_resource(FileMeta, '/entity/meta/<geid>')
nfs_entity_ns.add_resource(FileDetailBulk, '/bulk/detail')
nfs_entity_ns.add_resource(FileStatistics, '/project/<project_geid>/files/statistics')
nfs_entity_ns.add_resource(FileValidation, '/validation')
nfs_entity_ns.add_resource(FileRepeatedCheck, '/repeatcheck')

entity_ns_v2 = Namespace('File Operation V2', description='Operation on files', path='/v2/files')
entity_ns_v2.add_resource(FileMetaV2, '/meta')
entity_ns_v2.add_resource(FileDetailBulkV2, '/bulk/detail')


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
