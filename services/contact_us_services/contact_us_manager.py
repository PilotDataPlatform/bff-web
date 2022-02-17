from models.service_meta_class import MetaService
from models.invitation import InvitationForm
from models.contact_us import ContactUsForm
from services.notifier_services.email_service import SrvEmail
from services.data_providers.bff_rds import SrvRDSSingleton
from services.container_services.container_manager import SrvContainerManager
from services.logger_services.logger_factory_service import SrvLoggerFactory
from resources.utils import helper_now_utc
from config import ConfigClass
from hashlib import md5
import json
from datetime import timedelta

class SrvContactUsManager(metaclass=MetaService):

    def __init__(self):
        self._logger = SrvLoggerFactory('api_contact_use').get_logger()

    def save_invitation(self, invitation: ContactUsForm, access_token, current_identity):
        email_sender = SrvEmail()
        container_mgr = SrvContainerManager()

        subject = f"ACTION REQUIRED - {ConfigClass.PROJECT_NAME} Support Request Submitted"
        email_sender.send(
            subject,
            [ConfigClass.EMAIL_SUPPORT],
            msg_type='html',
            attachments=invitation.attachments,
            template="contact_us/support_email.html",
            template_kwargs={
                "title": invitation.title,
                "category": invitation.category, 
                "description": invitation.description, 
                "user_email": invitation.email, 
            }
        )

        confirm_subject = "Confirmation of Contact Email"
        email_sender.send(
            confirm_subject,
            [invitation.email],
            msg_type='html',
            attachments=invitation.attachments,
            template="contact_us/confirm_email.html",
            template_kwargs={
                "title": invitation.title,
                "category": invitation.category, 
                "description": invitation.description, 
                "email": ConfigClass.EMAIL_SUPPORT, 
            }
        )
        return 'Saved'

    def deactivate_invitation(self):
        pass
