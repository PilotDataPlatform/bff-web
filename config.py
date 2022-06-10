import os
from functools import lru_cache
from typing import Any
from typing import Dict
from typing import List

from pydantic import BaseSettings
from pydantic import Extra
from common import VaultClient
from dotenv import load_dotenv

load_dotenv()
SRV_NAMESPACE = os.environ.get("APP_NAME", "core")
CONFIG_CENTER_ENABLED = os.environ.get("CONFIG_CENTER_ENABLED", "false")


def load_vault_settings(settings: BaseSettings) -> Dict[str, Any]:
    if CONFIG_CENTER_ENABLED == "false":
        return {}
    else:
        return vault_factory()


def vault_factory() -> dict:
    vc = VaultClient(os.getenv("VAULT_URL"), os.getenv("VAULT_CRT"), os.getenv("VAULT_TOKEN"))
    return vc.get_from_vault(SRV_NAMESPACE)


class Settings(BaseSettings):
    """Store service configuration settings."""

    env: str = ""
    APP_NAME: str = 'core'
    version: str = "0.1.0"
    port: int = 5063
    host: str = "127.0.0.1"

    PROJECT_NAME: str

    # the packaged modules
    # api_modules = ["dataset"]
    api_modules: List[str] = ["api"]

    TIMEZONE: str = "CET"

    USERNAME_REGEX: str = "^[a-z\d]{6,20}$"
    PROJECT_CODE_REGEX: str = "^[a-z][a-z0-9]{0,31}$"
    PROJECT_NAME_REGEX: str = "^.{1,100}$"

    CORE_ZONE_LABEL: str
    GREENROOM_ZONE_LABEL: str

    PROJECT_NAME: str

    KEYCLOAK_REALM: str

    AD_USER_GROUP: str
    AD_PROJECT_GROUP_PREFIX: str

    # Services

    ENTITYINFO_SERVICE: str
    CATALOGUING_SERVICE: str
    DATA_OPS_UTIL: str
    NEO4J_SERVICE: str
    AUTH_SERVICE: str
    PROVENANCE_SERVICE: str
    NOTIFY_SERVICE: str
    EMAIL_SERVICE: str
    DATA_UPLOAD_SERVICE_CORE: str
    DATA_UPLOAD_SERVICE_GREENROOM: str
    DATASET_SERVICE: str
    DOWNLOAD_SERVICE_CORE: str
    DOWNLOAD_SERVICE_GR: str
    APPROVAL_SERVICE: str
    METADATA_SERVICE: str
    PROJECT_SERVICE: str

    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_PASSWORD: str

    # KONG API Gateway
    KONG_BASE: str
    KONG_PATH: str

    # Knowledge Graph
    KG_SERVICE: str
    KG_SERVICE_STAGE: str = "http://kg.utility:5081"

    # JWT
    JWT_AUTH_URL_RULE: None = None

    # Email addresses
    EMAIL_SUPPORT: str
    EMAIL_ADMIN: str
    EMAIL_HELPDESK: str

    # LDAP configs
    LDAP_URL: str
    LDAP_ADMIN_DN: str
    LDAP_ADMIN_SECRET: str
    LDAP_OU: str
    LDAP_DC1: str
    LDAP_DC2: str
    LDAP_objectclass: str

    # Domain
    SITE_DOMAIN: str

    # Invitation
    INVITATION_URL_LOGIN: str

    # Resource request
    RESOURCE_REQUEST_ADMIN: str

    # BFF RDS
    RDS_HOST: str
    RDS_PORT: str
    RDS_DBNAME: str
    RDS_USER: str
    RDS_PWD: str
    RDS_SCHEMA_DEFAULT: str
    ICON_SIZE_LIMIT: int = 500 * 1000

    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_HTTPS: bool = False

    RESOURCES: List[str] = ["SuperSet", "Guacamole"]

    OPEN_TELEMETRY_ENABLED: bool = False
    OPEN_TELEMETRY_HOST: str = '127.0.0.1'
    OPEN_TELEMETRY_PORT: int = 6831

    COLLAB_TEST_PASS: str = ""

    def modify_values(self, settings):
        ENTITYINFO_HOST = settings.ENTITYINFO_SERVICE
        settings.ENTITYINFO_SERVICE = ENTITYINFO_HOST + "/v1/"
        settings.ENTITYINFO_SERVICE_V2 = ENTITYINFO_HOST + "/v2/"
        settings.METADATA_SERVICE = settings.METADATA_SERVICE + "/v1/"
        settings.APPROVAL_SERVICE = settings.APPROVAL_SERVICE + "/v1/"
        CATALOGUING_HOST = settings.CATALOGUING_SERVICE
        settings.CATALOGUING_SERVICE = CATALOGUING_HOST + "v1/"
        settings.CATALOGUING_SERVICE_v2 = CATALOGUING_HOST + "/v2/"
        DATA_UTILITY_HOST = settings.DATA_OPS_UTIL
        settings.DATA_UTILITY_SERVICE = DATA_UTILITY_HOST + "/v1/"
        settings.DATA_UTILITY_SERVICE_v2 = DATA_UTILITY_HOST + "/v2/"
        NEO4J_HOST = settings.NEO4J_SERVICE
        settings.NEO4J_SERVICE = NEO4J_HOST + "/v1/neo4j/"
        settings.NEO4J_SERVICE_V2 = NEO4J_HOST + "/v2/neo4j/"
        settings.AUTH_SERVICE = settings.AUTH_SERVICE + "/v1/"
        settings.PROVENANCE_SERVICE = settings.PROVENANCE_SERVICE + "/v1/"
        settings.NOTIFY_SERVICE = settings.NOTIFY_SERVICE
        settings.EMAIL_SERVICE = settings.EMAIL_SERVICE + "/v1/email"
        settings.DATA_UPLOAD_SERVICE_CORE = settings.DATA_UPLOAD_SERVICE_CORE + "/v1"
        settings.DATA_UPLOAD_SERVICE_GREENROOM = settings.DATA_UPLOAD_SERVICE_GREENROOM + "/v1"
        settings.DATASET_SERVICE = settings.DATASET_SERVICE + "/v1/"
        settings.DOWNLOAD_SERVICE_CORE_V2 = settings.DOWNLOAD_SERVICE_CORE + "/v2/"
        settings.DOWNLOAD_SERVICE_GR_V2 = settings.DOWNLOAD_SERVICE_GR + "/v2/"

        settings.KONG_BASE = settings.KONG_BASE + settings.KONG_PATH
        settings.KG_SERVICE = settings.KG_SERVICE + "/v1/" if settings.env == "test" else settings.KG_SERVICE_STAGE + "/v1/"

        settings.OPS_DB_URI = f"postgresql://{settings.RDS_USER}:{settings.RDS_PWD}@{settings.RDS_HOST}/{settings.RDS_DBNAME}"
        settings.SQLALCHEMY_DATABASE_URI = f"postgresql://{settings.RDS_USER}:{settings.RDS_PWD}@{settings.RDS_HOST}/{settings.RDS_DBNAME}"

        settings.REDIS_URL = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        return settings

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = Extra.allow

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return env_settings, load_vault_settings, init_settings, file_secret_settings


@lru_cache(1)
def get_settings():
    settings = Settings()
    settings = settings.modify_values(settings)
    return settings


ConfigClass = get_settings()
