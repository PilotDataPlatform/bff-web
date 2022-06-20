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
from app import db
from datetime import datetime
from config import ConfigClass

class ResourceRequest(db.Model):
    __tablename__ = 'resource_request'
    __table_args__ = {"schema":ConfigClass.RDS_SCHEMA_DEFAULT}
    id = db.Column(db.Integer, unique=True, primary_key=True)
    user_id = db.Column(db.String())
    username = db.Column(db.String())
    email = db.Column(db.String())
    project_geid = db.Column(db.String())
    project_name = db.Column(db.String())
    request_date = db.Column(db.DateTime(), default=datetime.utcnow)
    request_for = db.Column(db.String())
    active = db.Column(db.Boolean(), default=True)
    complete_date = db.Column(db.DateTime())

    def __init__(self, user_id, username, email, project_geid, project_name, request_for):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.project_geid = project_geid
        self.project_name = project_name
        self.request_for = request_for

    def to_dict(self):
        result = {}
        for field in ["id", "user_id", "username", "email", "project_geid", "project_name", "request_date", \
                "request_for", "active", "complete_date"]:
            if field in ["complete_date", "request_date"]:
                result[field] = str(getattr(self, field))
            else:
                result[field] = getattr(self, field)
        return result
