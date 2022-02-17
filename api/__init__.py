from .module_api import module_api
from .api_hello_world import APIHelloWorld
from .api_invitation import APIInvitation
from .api_auth import APIAuthService
from .api_contact_us import APIContactUs
# from .api_cataloguing import APICataloguing
from .api_time import APITimestamp
from .api_email import APIEmail
from .api_notification.notification import APINotification, APINotifications
from .api_notification.unsubscribe import APIUnsubscribe
from .api_container.route_registry import APIContainer
from .api_data_manifest.data_manifest import APIDataManifest
from .api_project import APIProject
from .api_project_v2 import APIProjectV2
from .api_system_tags import APISystemTags
from .api_announcement.announcement import APIAnnouncement
from .api_users import APIUsers
from .api_provenance import APIProvenance
from .api_scripts.neo_to_es import APINeo4j2ESScript
from .api_resource_request.resource_request import APIResourceRequest
from .api_workbench import APIWorkbench
from .api_folder_creation.api_folder_ops_v1 import APIFolderCreation
from .api_tags.api_tags_operation import APITagsV2
from .api_tags.api_batch_tags_operation import APIBatchTagsV2
from .api_archive import APIArchive
from .api_preview import APIPreview
from .api_dataset_rest_proxy import APIDatasetProxy, APIDatasetFileProxy, \
    APIDatasetFileRenameProxy, APIDatasetFileTasks
from .api_download import APIDatasetDownload
from .api_dataset.api_activity_logs import APIDatasetActivityLogs
from .api_dataset.api_versions import APIVersions
from .api_dataset.api_folder import APIDatasetFolder
from .api_dataset.api_schema import APISchema
from .api_dataset.api_schema_template import APIDatasetSchemaTemplateProxy
from .api_dataset.api_validate import APIValidator
from .api_kg.api_kg_resource import APIKGResourceProxy
from .api_copy_request.copy_request import APICopyRequest
from .api_upload_ops import APIFileUploadStatus

apis = [
    APIHelloWorld(),
    APIInvitation(),
    APIContainer(),
    APIAuthService(),
    APIContactUs(),
    # APICataloguing(),
    APITimestamp(),
    APIEmail(),
    APIDataManifest(),
    APIProject(),
    APIProjectV2(),
    APISystemTags(),
    APIAnnouncement(),
    APINotification(),
    APINotifications(),
    APIUnsubscribe(),
    APIUsers(),
    APIProvenance(),
    APINeo4j2ESScript(),
    APIResourceRequest(),
    # APIResourceRequestV2(),
    APIWorkbench(),
    APIFolderCreation(),
    APITagsV2(),
    APIBatchTagsV2(),
    APIArchive(),
    APIPreview(),
    APIDatasetProxy(),
    APIDatasetFileProxy(),
    APIDatasetFileRenameProxy(),
    APIDatasetFileTasks(),
    APIDatasetDownload(),
    APIDatasetActivityLogs(),
    APIVersions(),
    APIDatasetFolder(),
    APISchema(),
    APIDatasetSchemaTemplateProxy(),
    APIValidator(),
    APIKGResourceProxy(),
    APICopyRequest(),
    APIFileUploadStatus()
]


def api_registry(apis):
    if len(apis) > 0:
        for api_sub_module in apis:
            api_sub_module.api_registry()
    else:
        print('[Fatal]', 'No API registered.')


api_registry(apis)
