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
from models.service_meta_class import MetaService
from config import ConfigClass
import requests
import json


class SrvEmail(metaclass=MetaService):
    def send(self, subject, receiver: list = [], content=None, msg_type="plain", attachments=[], \
            sender=ConfigClass.EMAIL_SUPPORT, template=None, template_kwargs={}):
        '''
        (str, str, str, str, str) -> dict   #**TypeContract**
        '''
        url = ConfigClass.EMAIL_SERVICE
        payload = {
            "subject": subject,
            "sender": sender,
            "receiver": receiver,
            "msg_type": msg_type,
            "attachments": attachments,
        }
        if content:
            payload["message"] = content
        if template:
            payload["template"] = template
            payload["template_kwargs"] = template_kwargs
        res = requests.post(
            url=url,
            json=payload
        )
        return json.loads(res.text)
