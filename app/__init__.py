import importlib
import json

import jwt as pyjwt
import requests
from flask import request
from flask_cors import CORS
from flask_executor import Executor
from flask_jwt import JWT
from flask_jwt import JWTError
from flask_sqlalchemy import SQLAlchemy
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.resources import SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.flask import Flask
from config import ConfigClass
from config import get_settings
from services.logger_services.logger_factory_service import SrvLoggerFactory


def create_db(app):
    db = SQLAlchemy()
    db.init_app(app)
    return db


executor = Executor()
app = Flask(__name__, static_folder="../build/static", template_folder="../build")
app.config['SQLALCHEMY_DATABASE_URI'] = ConfigClass.SQLALCHEMY_DATABASE_URI
db = create_db(app)


def create_app():
    # initialize app and config app
    app.config.from_object(__name__ + '.ConfigClass')
    CORS(
        app,
        origins="*",
        allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
        supports_credentials=True,
        intercept_exceptions=False,
    )

    # initialize flask executor
    executor.init_app(app)

    # dynamic add the dataset module by the config we set
    for apis in ConfigClass.api_modules:
        # print(apis)
        api = importlib.import_module(apis)
        api.module_api.init_app(app)

    jwt = JWT(app)

    @jwt.jwt_error_handler
    def error_handler(e):
        print("###### Error Handler")
        # Either not Authorized or Expired
        print(e)
        return {'result': 'jwt ' + str(e)}, 401

    # load jwt token from request's header
    @jwt.request_handler
    def load_token():
        print("###### Load Token")
        token = request.headers.get('Authorization')
        print(request.headers)

        if not token:
            return token

        return token.split()[-1]

    # function is to parse out the infomation in the JWT
    @jwt.jwt_decode_handler
    def decode_auth_token(token):
        print("###### decode_auth_token by syncope")
        try:
            decoded = pyjwt.decode(token, verify=False)
            return decoded
        except Exception as e:
            raise JWTError(description='Error', error=e)

    # finally we pass the infomation to here to identify the user
    @jwt.identity_handler
    def identify(payload):
        print("###### identify")
        username = payload.get('preferred_username', None)

        _logger = SrvLoggerFactory('jwt_identify').get_logger()

        # check if preferred_username is encoded in token
        if not username:
            raise Exception("preferred_username is required in jwt token.")

        try:
            # check if user is existed in neo4j
            url = ConfigClass.NEO4J_SERVICE + "nodes/User/query"
            res = requests.post(
                url=url,
                json={"name": username}
            )
            if res.status_code != 200:
                raise Exception("Neo4j service: " + json.loads(res.text))
            users = json.loads(res.text)
            if len(users) == 0:
                raise Exception(
                    "Neo4j service: User %s does not exist." % username)
            user_id = users[0]['id']
            email = users[0]['email']
            first_name = users[0]['first_name']
            last_name = users[0]['last_name']

            _logger.info(str(users))

            role = None
            if 'role' in users[0]:
                role = users[0]['role']

        except Exception as e:
            _logger.error(str(e))
            raise JWTError(description='Error', error=e)
        try:
            realm_roles = payload["realm_access"]["roles"]
        except Exception as e:
            _logger.error("Couldn't get realm roles" + str(e))
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

    instrument_app(app)

    return app


def instrument_app(app: Flask) -> None:
    """Instrument the application with OpenTelemetry tracing."""

    settings = get_settings()

    if not settings.OPEN_TELEMETRY_ENABLED:
        return

    tracer_provider = TracerProvider(resource=Resource.create({SERVICE_NAME: settings.APP_NAME}))
    trace.set_tracer_provider(tracer_provider)

    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()

    jaeger_exporter = JaegerExporter(
        agent_host_name=settings.OPEN_TELEMETRY_HOST, agent_port=settings.OPEN_TELEMETRY_PORT
    )

    tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
