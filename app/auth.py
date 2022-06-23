from fastapi import Request

import jwt as pyjwt
from config import ConfigClass, SRV_NAMESPACE
from common import LoggerFactory
import httpx
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


logger = LoggerFactory('jwt_identify').get_logger()


async def jwt_required(request: Request):
    current_identity = get_current_identity(request)
    if not current_identity:
        raise Exception("couldn't get user from jwt")
    return current_identity


def get_current_identity(request: Request):
    token = request.headers.get('Authorization')
    token = token.split()[-1]
    payload = pyjwt.decode(token, verify=False)
    username: str = payload.get("preferred_username")

    if not username:
        return None

    # check if user is existed in neo4j
    data = {
        "username": username,
        "exact": True,
    }
    response = httpx.get(ConfigClass.AUTH_SERVICE + "admin/user", params=data)
    if response.status_code != 200:
        raise Exception(f"Error getting user {username} from auth service: " + response.json())

    user = response.json()["result"]
    if not user:
        return None

    if user["attributes"].get("status") != "active":
        return None

    user_id = user['id']
    email = user['email']
    first_name = user['first_name']
    last_name = user['last_name']
    role = None
    if 'role' in user:
        role = user['role']

    try:
        realm_roles = payload["realm_access"]["roles"]
    except Exception as e:
        logger.error("Couldn't get realm roles" + str(e))
        realm_roles = []
    return {
        "user_id": user_id,
        "username": username,
        "role": role,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "realm_roles": realm_roles,
    }


def instrument_app(app) -> None:
    """Instrument the application with OpenTelemetry tracing."""

    tracer_provider = TracerProvider(resource=Resource.create({SERVICE_NAME: SRV_NAMESPACE}))
    trace.set_tracer_provider(tracer_provider)

    jaeger_exporter = JaegerExporter(
        agent_host_name=ConfigClass.OPEN_TELEMETRY_HOST, agent_port=ConfigClass.OPEN_TELEMETRY_PORT
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
