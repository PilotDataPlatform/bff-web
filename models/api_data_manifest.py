from enum import Enum
import datetime
from flask_sqlalchemy import SQLAlchemy
from config import ConfigClass
from app import db


class TypeEnum(Enum):
    text = 'text'
    multiple_choice = 'multiple_choice'


class DataManifestModel(db.Model):
    __tablename__ = 'data_manifest'
    __table_args__ = {"schema":ConfigClass.RDS_SCHEMA_DEFAULT}
    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.String())
    project_code = db.Column(db.String())

    def __init__(self, name, project_code):
        self.name = name
        self.project_code = project_code 

    def to_dict(self):
        result = {}
        for field in ["id", "name", "project_code"]:
            result[field] = getattr(self, field)
        return result 


class DataAttributeModel(db.Model):
    __tablename__ = 'data_attribute'
    __table_args__ = {"schema":ConfigClass.RDS_SCHEMA_DEFAULT}
    id = db.Column(db.Integer, unique=True, primary_key=True)
    manifest_id = db.Column(db.Integer, db.ForeignKey(DataManifestModel.id))
    name = db.Column(db.String())
    type = db.Column(db.Enum(TypeEnum), default="text", nullable=False)
    value = db.Column(db.String())
    project_code = db.Column(db.String())
    optional = db.Column(db.Boolean(), default=False)

    def __init__(self, manifest_id, name, type, value, project_code, optional):
        self.name = name
        self.type = type 
        self.value = value 
        self.project_code = project_code 
        self.optional = optional 
        self.manifest_id = manifest_id

    def to_dict(self):
        result = {}
        for field in ["id", "name", "type", "value", "project_code", "optional", "manifest_id"]:
            result[field] = getattr(self, field)
        result["type"] = result["type"].value
        return result 


class DataManifest:
    def __init__(self):
        timestamp = round(datetime.datetime.utcnow().timestamp())
        self.__attribute_map = {
            "manifest_id": None,
            "key": "",
            "diplay_name": "",
            "value": "",
            "note": "",
            "type": "",
            "create_timestamp": timestamp,
            "update_timestamp": timestamp,
            "optional": True,
        }

    @property
    def to_dict(self):
        '''
        property not function
        '''
        return self.__attribute_map

    @property
    def manifest_id(self):
        return self.__attribute_map['manifest_id']
    @manifest_id.setter
    def manifest_id(self, my_id: str):
        self.__attribute_map['manifest_id'] = my_id

    @property
    def key(self):
        return self.__attribute_map['key']
    @key.setter
    def key(self, key: str):
        self.__attribute_map['key'] = key

    @property
    def diplay_name(self):
        return self.__attribute_map['diplay_name']
    @diplay_name.setter
    def diplay_name(self, diplay_name: str):
        self.__attribute_map['diplay_name'] = diplay_name

    @property
    def value(self):
        return self.__attribute_map['value']
    @value.setter
    def value(self, value: str):
        self.__attribute_map['value'] = value

    @property
    def note(self):
        return self.__attribute_map['note']
    @note.setter
    def note(self, note: str):
        self.__attribute_map['note'] = note

    @property
    def type(self):
        return self.__attribute_map['type']
    @type.setter
    def type(self, type: str):
        self.__attribute_map['type'] = type

    @property
    def create_timestamp(self):
        return self.__attribute_map['create_timestamp']
    @create_timestamp.setter
    def create_timestamp(self, create_timestamp: int):
        self.__attribute_map['create_timestamp'] = create_timestamp

    @property
    def update_timestamp(self):
        return self.__attribute_map['update_timestamp']
    @update_timestamp.setter
    def update_timestamp(self, update_timestamp: int):
        self.__attribute_map['update_timestamp'] = update_timestamp

    @property
    def optional(self):
        return self.__attribute_map['optional']
    @optional.setter
    def optional(self, optional: bool):
        self.__attribute_map['optional'] = optional

class EDataManifestType(Enum):
    ONE_CHOICE = 0,
    MULTIPLE_CHOICE = 1,
    INPUT_STRING = 2,
    SUB_MANIFEST = 3
