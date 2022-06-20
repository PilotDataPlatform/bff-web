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
from .module_api import module_api
from .api_invitation import APIInvitation
from .api_auth import APIAuthService
from .api_contact_us import APIContactUs
# from .api_cataloguing import APICataloguing
from .api_email import APIEmail
from .api_notification.notification import APINotification, APINotifications
from .api_notification.unsubscribe import APIUnsubscribe
from .api_container.route_registry import APIContainer
from .api_data_manifest.data_manifest import APIDataManifest
from .api_project import APIProject
from .api_project_v2 import APIProjectV2
from .api_announcement.announcement import APIAnnouncement
from .api_users import APIUsers
from .api_provenance import APIProvenance
from .api_resource_request.resource_request import APIResourceRequest
from .api_workbench import APIWorkbench
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
from .api_user_event.event import APIEvent

apis = [
    APIInvitation(),
    APIContainer(),
    APIAuthService(),
    APIContactUs(),
    # APICataloguing(),
    APIEmail(),
    APIDataManifest(),
    APIProject(),
    APIProjectV2(),
    APIAnnouncement(),
    APINotification(),
    APINotifications(),
    APIUnsubscribe(),
    APIUsers(),
    APIProvenance(),
    APIResourceRequest(),
    # APIResourceRequestV2(),
    APIWorkbench(),
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
    APIEvent(),
]


def api_registry(apis):
    if len(apis) > 0:
        for api_sub_module in apis:
            api_sub_module.api_registry()
    else:
        print('[Fatal]', 'No API registered.')


api_registry(apis)
