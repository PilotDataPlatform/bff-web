import flask
from werkzeug.utils import cached_property


class Request(flask.Request):
    """Request object used by default in Flask."""

    @cached_property
    def headers(self):
        """Return mutable copy of headers.

        This allows OpenTelemetry update headers when they are passed to subsequent requests.
        """

        return dict(super().headers)


class Flask(flask.Flask):
    """Flask main application object with overridden classes."""

    request_class = Request
