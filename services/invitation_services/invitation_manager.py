from models.service_meta_class import MetaService
from models.invitation import InvitationForm, InvitationModel, db
from models.user_type import map_neo4j_to_frontend
from services.notifier_services.email_service import SrvEmail
from services.data_providers.bff_rds import SrvRDSSingleton
from services.container_services.container_manager import SrvContainerManager
from services.logger_services.logger_factory_service import SrvLoggerFactory
from services.neo4j_service.neo4j_client import Neo4jClient
from resources.utils import helper_now_utc
from config import ConfigClass
from hashlib import md5
import json
import base64
from datetime import timedelta, datetime


class SrvInvitationManager(metaclass=MetaService):

    def __init__(self):
        self._logger = SrvLoggerFactory('api_invitation').get_logger()

    def update_invitation(self, query_data, update_data):
        try:
            db.session.query(InvitationModel).filter_by(
                **query_data).update(update_data)
            db.session.commit()
        except Exception as e:
            self._logger.error("Failed to update SQL record: " + str(e))
            return str(e)
        return 'success'

    def save_invitation(self, invitation: InvitationModel, access_token, current_identity, status="pending", ad_account_created=False, ad_first=None):
        invitor_name = current_identity['username']
        email_sender = SrvEmail()
        container_mgr = SrvContainerManager()
        now_utc_dt = helper_now_utc()
        create_timestamp = now_utc_dt.isoformat()

        form_data = invitation.to_dict
        form_data_json = json.dumps(form_data)

        sql_params = {
            "invitation_detail": form_data_json,
            "create_timestamp": create_timestamp,
            "expiry_timestamp": create_timestamp,  # TODO remove when SQL is updated
            "invited_by": invitor_name,
            "email": invitation.email,
            "role": invitation.platform_role,
            "project": str(invitation.project_id),
            "invite_by": str(invitation.inviter),
            "status": status,
        }
        if invitation.project_id:
            sql_params["role"] = invitation.project_role
        inserted = InvitationModel(**sql_params)
        db.session.add(inserted)
        db.session.commit()
        db.session.refresh(inserted)

        neo4j_client = Neo4jClient()
        response = neo4j_client.get_user_by_username(invitor_name)
        if response.get("code") != 200:
            return response
        inviter_node = response["result"]

        self._logger.info(f'Invitation {inserted.id} Saved To Database')
        first_name = inviter_node.get("first_name", inviter_node["name"])
        last_name = inviter_node.get("last_name", "")
        inviter_name = f"{first_name} {last_name}"

        if invitation.project_id:
            my_project = container_mgr.check_container_exist(
                access_token, "Container", invitation.project_id)[0]
            my_project_name = my_project['name']
            self._logger.info(my_project)
            subject = "Welcome to the {} project!".format(my_project_name)
            if not ad_account_created:
                template = "invitation/ad_invite_project.html"
            else:
                template = "invitation/ad_existing_invite_project.html"

            template_kwargs = {
                "inviter_email": inviter_node["email"],
                "inviter_name": inviter_name,
                "project_name": my_project_name,
                "project_code": my_project["code"],
                "project_role": map_neo4j_to_frontend(invitation.project_role),
                "support_email": ConfigClass.EMAIL_SUPPORT,
                "admin_email": ConfigClass.EMAIL_ADMIN,
                "url": ConfigClass.INVITATION_URL_LOGIN,
                "user_email": invitation.email,
                "domain": ConfigClass.SITE_DOMAIN,
                "helpdesk_email": ConfigClass.EMAIL_HELPDESK,
                "user_first": ad_first,
            }
        else:
            subject = f"Welcome to {ConfigClass.PROJECT_NAME}!"
            if not ad_account_created:
                template = "invitation/ad_invite_without_project.html"
            else:
                template = "invitation/ad_existing_invite_without_project.html"

            if invitation.platform_role == "admin":
                platform_role = "Platform Administrator"
            else:
                platform_role = "Platform User"
            template_kwargs = {
                "inviter_email": inviter_node["email"],
                "inviter_name": inviter_name,
                "support_email": ConfigClass.EMAIL_SUPPORT,
                "admin_email": ConfigClass.EMAIL_ADMIN,
                "platform_role": platform_role,
                "url": ConfigClass.INVITATION_URL_LOGIN,
                "user_email": invitation.email,
                "domain": ConfigClass.SITE_DOMAIN,
                "helpdesk_email": ConfigClass.EMAIL_HELPDESK,
                "user_first": ad_first,
            }
        with open("attachments/Invite-AD-Application.pdf", 'rb') as f:
            if not ad_account_created:
                data = base64.b64encode(f.read()).decode()
                attachment = [
                    {"name": "AD Request Form.pdf", "data": data}]
            else:
                attachment = []
            email_sender.send(
                subject,
                [invitation.email],
                msg_type='html',
                template=template,
                template_kwargs=template_kwargs,
                attachments=attachment,
            )
            if not ad_account_created:
                # send copy to admin
                email_sender.send(
                    subject,
                    [ConfigClass.EMAIL_ADMIN],
                    msg_type='html',
                    template=template,
                    template_kwargs=template_kwargs,
                    attachments=attachment,
                )
        return 'Saved'

    def get_invitations(self, page, page_size, filters, order_by, order_type):
        if not filters:
            filters = {}

        sql_filter = {}
        if "project_id" in filters:
            sql_filter["project"] = str(filters["project_id"])
        if "status" in filters:
            sql_filter["status"] = filters["status"]

        invites = db.session.query(InvitationModel).filter_by(**sql_filter)
        if "email" in filters:
            invites = invites.filter(
                InvitationModel.invitation_detail.like("%" + filters["email"] + "%"))
        if "invited_by" in filters:
            invites = invites.filter(InvitationModel.invited_by.like(
                "%" + filters["invited_by"] + "%"))

        if not order_by:
            order_by = "create_timestamp"
        if order_type == "desc":
            sort_param = getattr(InvitationModel, order_by).desc()
        else:
            sort_param = getattr(InvitationModel, order_by).asc()
        invites = invites.order_by(sort_param)
        count = len(invites.all())
        invites = invites.offset(page * page_size).limit(page_size).all()
        return invites, count
