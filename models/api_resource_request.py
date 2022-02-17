from app import db
from datetime import datetime
from config import ConfigClass

class ResourceRequest(db.Model):
    __tablename__ = 'resource_request'
    __table_args__ = {"schema":ConfigClass.RDS_SCHEMA_DEFAULT}
    id = db.Column(db.Integer, unique=True, primary_key=True)
    user_geid = db.Column(db.String())
    username = db.Column(db.String())
    email = db.Column(db.String())
    project_geid = db.Column(db.String())
    project_name = db.Column(db.String())
    request_date = db.Column(db.DateTime(), default=datetime.utcnow)
    request_for = db.Column(db.String())
    active = db.Column(db.Boolean(), default=True)
    complete_date = db.Column(db.DateTime())

    def __init__(self, user_geid, username, email, project_geid, project_name, request_for):
        self.user_geid = user_geid
        self.username = username
        self.email = email
        self.project_geid = project_geid
        self.project_name = project_name
        self.request_for = request_for

    def to_dict(self):
        result = {}
        for field in ["id", "user_geid", "username", "email", "project_geid", "project_name", "request_date", \
                "request_for", "active", "complete_date"]:
            if field in ["complete_date", "request_date"]:
                result[field] = str(getattr(self, field))
            else:
                result[field] = getattr(self, field)
        return result
