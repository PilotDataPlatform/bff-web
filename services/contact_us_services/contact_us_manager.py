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
from common import LoggerFactory

from config import ConfigClass
from models.contact_us import ContactUsForm
from models.service_meta_class import MetaService
from services.notifier_services.email_service import SrvEmail


class SrvContactUsManager(metaclass=MetaService):
    def __init__(self):
        self._logger = LoggerFactory('api_contact_use').get_logger()

    def send_contact_us_email(self, contact_us_form: ContactUsForm):
        email_sender = SrvEmail()

        subject = f'ACTION REQUIRED - {ConfigClass.PROJECT_NAME} Support Request Submitted'
        email_sender.send(
            subject,
            [ConfigClass.EMAIL_SUPPORT],
            msg_type='html',
            attachments=contact_us_form.attachments,
            template='contact_us/support_email.html',
            template_kwargs={
                'title': contact_us_form.title,
                'category': contact_us_form.category,
                'description': contact_us_form.description,
                'user_email': contact_us_form.email,
            },
        )

        confirm_subject = 'Confirmation of Contact Email'
        email_sender.send(
            confirm_subject,
            [contact_us_form.email],
            msg_type='html',
            attachments=contact_us_form.attachments,
            template='contact_us/confirm_email.html',
            template_kwargs={
                'title': contact_us_form.title,
                'category': contact_us_form.category,
                'description': contact_us_form.description,
                'email': ConfigClass.EMAIL_SUPPORT,
            },
        )
