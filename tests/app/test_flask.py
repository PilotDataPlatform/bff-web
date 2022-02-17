from flask import request

from app.flask import Request


class TestRequest:

    def test_headers_returns_dict(self, request_context):
        assert isinstance(request.headers, dict) is True


class TestFlask:

    def test_app_uses_overridden_request_class(self, app):
        assert app.request_class is Request
