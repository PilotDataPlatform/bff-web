import json
from datetime import timedelta
from hashlib import md5

from common import LoggerFactory

from config import ConfigClass
from models.contact_us import ContactUsForm
from models.service_meta_class import MetaService
from resources.utils import helper_now_utc
from services.notifier_services.email_service import SrvEmail


class SrvContactUsManager(metaclass=MetaService):
    def __init__(self):
        self._logger = LoggerFactory('api_contact_use').get_logger()

    def save_invitation(self, invitation: ContactUsForm, access_token, current_identity):
        email_sender = SrvEmail()

        subject = f'ACTION REQUIRED - {ConfigClass.PROJECT_NAME} Support Request Submitted'
        email_sender.send(
            subject,
            [ConfigClass.EMAIL_SUPPORT],
            msg_type='html',
            attachments=invitation.attachments,
            template='contact_us/support_email.html',
            template_kwargs={
                'title': invitation.title,
                'category': invitation.category,
                'description': invitation.description,
                'user_email': invitation.email,
            },
        )

        confirm_subject = 'Confirmation of Contact Email'
        email_sender.send(
            confirm_subject,
            [invitation.email],
            msg_type='html',
            attachments=invitation.attachments,
            template='contact_us/confirm_email.html',
            template_kwargs={
                'title': invitation.title,
                'category': invitation.category,
                'description': invitation.description,
                'email': ConfigClass.EMAIL_SUPPORT,
            },
        )
        return 'Saved'

    def deactivate_invitation(self):
        pass
