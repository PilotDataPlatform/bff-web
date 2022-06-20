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
