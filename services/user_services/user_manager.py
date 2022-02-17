import requests
import json
from models.service_meta_class import MetaService
from config import ConfigClass


class SrvUserManager(metaclass=MetaService):
    def __init__(self):
        self.url = ConfigClass.NEO4J_SERVICE

    def get_email_by_username(self, username):
        url = ConfigClass.NEO4J_SERVICE + "nodes/User/query"
        res = requests.post(
            url=url,
            json={"name": username}
        )
        users = json.loads(res.text)
        return users[0]['email']
    
    def get_user_by_email(self, email):
        url = ConfigClass.NEO4J_SERVICE + "nodes/User/query"
        res = requests.post(
            url=url,
            json={"email": email}
        )
        users = json.loads(res.text)
        return users[0]
