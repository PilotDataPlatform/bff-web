import os

import pytest

from app import Flask


@pytest.fixture
def app():
    app = Flask('flask_test', root_path=os.path.dirname(__file__))
    return app


@pytest.fixture
def request_context(app):
    with app.test_request_context() as context:
        yield context
