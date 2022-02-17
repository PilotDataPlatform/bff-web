from app import db
from config import ConfigClass


class InvitationModel(db.Model):
    __tablename__ = 'user_invitation'
    __table_args__ = {"schema":ConfigClass.RDS_SCHEMA_DEFAULT}
    id = db.Column(db.Integer, unique=True, primary_key=True)
    invitation_code = db.Column(db.String())
    invitation_detail = db.Column(db.String())
    expiry_timestamp = db.Column(db.DateTime())
    create_timestamp = db.Column(db.DateTime())
    invited_by = db.Column(db.String())
    email = db.Column(db.String())
    role = db.Column(db.String())
    project = db.Column(db.String())
    status = db.Column(db.String())

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        result = {}
        field_list = [
            "id",
            "invitation_code",
            "invitation_detail",
            "expiry_timestamp",
            "create_timestamp",
            "invited_by",
            "email",
            "role",
            "project",
            "status",
        ]
        for field in field_list:
            result[field] = getattr(self, field)
        return result 


class InvitationForm:
    def __init__(self, event=None):
        if event:
            self._attribute_map = event
        else:
            self._attribute_map = {
                'email': '',  # by default success
                'projectId': -1,  # empty when success
                'platform_role': '',
                'project_role': '',
                'inviter': '',
            }

    @property
    def to_dict(self):
        return self._attribute_map

    @property
    def email(self):
        return self._attribute_map['email']

    @email.setter
    def email(self, email):
        self._attribute_map['email'] = email

    @property
    def project_id(self):
        return self._attribute_map.get('projectId')

    @project_id.setter
    def project_id(self, project_id):
        self._attribute_map['projectId'] = project_id

    @property
    def platform_role(self):
        return self._attribute_map.get('platform_role')

    @platform_role.setter
    def platform_role(self, role):
        self._attribute_map['platform_role'] = role

    @property
    def project_role(self):
        return self._attribute_map.get('project_role')

    @project_role.setter
    def project_role(self, role):
        self._attribute_map['project_role'] = role

    @property
    def inviter(self):
        return self._attribute_map.get('inviter')

    @inviter.setter
    def inviter(self, inviter):
        self._attribute_map['inviter'] = inviter
