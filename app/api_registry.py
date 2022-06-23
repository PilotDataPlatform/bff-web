from fastapi import FastAPI

from api import api_workbench
from api import api_invitation
from api import api_archive
from api.api_announcement import announcement
from api import api_auth
from api import api_contact_us
from api.api_container import api_aduser_update, api_container_user, api_containers, api_folder_creation, user_operation
from api.api_copy_request import copy_request
from api.api_data_manifest import data_manifest
from api import api_dataset_rest_proxy
from api.api_dataset import api_folder, api_schema, api_schema_template, api_validate, api_versions
from api import api_download
from api import api_email
from api.api_files import file_ops


def api_registry(app: FastAPI):
    app.include_router(api_workbench.router, prefix="/v1")
    app.include_router(api_invitation.router, prefix="/v1")
    app.include_router(announcement.router, prefix="/v1")
    app.include_router(api_archive.router, prefix="/v1")
    app.include_router(api_auth.router, prefix="/v1")
    app.include_router(api_contact_us.router, prefix="/v1")
    app.include_router(api_aduser_update.router, prefix="/v1")
    app.include_router(api_container_user.router, prefix="/v1")
    app.include_router(api_containers.router, prefix="/v1")
    app.include_router(api_folder_creation.router, prefix="/v1")
    app.include_router(user_operation.router, prefix="/v1")
    app.include_router(copy_request.router, prefix="/v1")
    app.include_router(data_manifest.router, prefix="/v1")
    app.include_router(api_dataset_rest_proxy.router, prefix="/v1")
    app.include_router(api_folder.router, prefix="/v1")
    app.include_router(api_schema.router, prefix="/v1")
    app.include_router(api_schema_template.router, prefix="/v1")
    app.include_router(api_validate.router, prefix="/v1")
    app.include_router(api_versions.router, prefix="/v1")
    app.include_router(api_download.router, prefix="/v1")
    app.include_router(api_email.router, prefix="/v1")
    app.include_router(file_ops.router, prefix="/v1")
