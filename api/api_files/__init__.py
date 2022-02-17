# from ..upload_ops import CheckUploadStateRestful
from .vfolder_ops import VirtualFolderFiles, VirtualFolder, VirtualFolderInfo
from .file_ops import FileActionLogs, FileActions, FileActionTasks, FileValidation, FileRepeatedCheck
from .file_ops_v2 import FileTags
from .file_ops_v4 import FileInfoV4
from .meta import FileMeta, FileMetaHome, FileDetail, FileDetailBulk
from .file_stats import FileStatistics
from .folder_entity import FolderEntity, FoldersEntity
from flask_restx import Api, Resource, fields, Namespace
from config import ConfigClass

nfs_entity_ns = Namespace(
    'NFS Data Operation', description='Operation on NFS', path='/v1/files')

nfs_entity_ns.add_resource(FileActionLogs, '/actions/logs')
nfs_entity_ns.add_resource(FileActions, '/actions')
nfs_entity_ns.add_resource(FileActionTasks, '/actions/tasks')
nfs_entity_ns.add_resource(FoldersEntity, '/entity/folders')
nfs_entity_ns.add_resource(FolderEntity, '/entity/folder/')
nfs_entity_ns.add_resource(FileMetaHome, '/entity/meta/')
nfs_entity_ns.add_resource(FileMeta, '/entity/meta/<geid>')
nfs_entity_ns.add_resource(FileDetail, '/detail/<file_geid>')
nfs_entity_ns.add_resource(FileDetailBulk, '/bulk/detail')
nfs_entity_ns.add_resource(FileStatistics, '/project/<project_geid>/files/statistics')
nfs_entity_ns.add_resource(FileValidation, '/validation')
nfs_entity_ns.add_resource(FileRepeatedCheck, '/repeatcheck')


nfs_entity_ns_v2 = Namespace(
    'NFS Data Operation Version 2', description='Operation on NFS', path='/v2/files'
)

#nfs_entity_ns_v2.add_resource(FileInfoV2, '/containers/<dataset_id>/files/meta')
# downstream service dataops_gr -> /containers/<dataset_id/tags is deprecated
nfs_entity_ns_v2.add_resource(FileTags, '/containers/<dataset_id>/files/tags')

nfs_upload_ns = Namespace(
    'NFS Data Upload', description='Upload on NFS', path='/v1/upload')

# downstream deprecated
# nfs_upload_ns.add_resource(CheckUploadStateRestful,
#                            '/containers/<container_id>/upload-state')

nfs_vfolder_ns = Namespace(
    'NFS Data vFolder', description='vFolder on NFS', path='/v1')
nfs_vfolder_ns.add_resource(VirtualFolderFiles, '/collections/<collection_geid>/files')
nfs_vfolder_ns.add_resource(VirtualFolder, '/collections')
nfs_vfolder_ns.add_resource(VirtualFolderInfo, '/collections/<collection_geid>')


# nfs_entity_ns_v4 = Namespace(
#     'File Search', description='File Search', path='/v1/<dataset_id>/files'
# )

nfs_entity_ns_v4 = Namespace(
    'File Search', description='File Search', path='/v1/<project_geid>/files'
)
nfs_entity_ns_v4.add_resource(FileInfoV4, '/search')
