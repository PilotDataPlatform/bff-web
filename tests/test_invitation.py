import unittest
from tests.prepare_test import SetUpTest, PrepareTest
from tests.logger import Logger
from unittest import mock
import json
from models.invitation import InvitationModel, db
from services.notifier_services.email_service import SrvEmail
import requests
from config import ConfigClass

class TestInvitation(unittest.TestCase):
    log = Logger(name='test_invitation.log')
    test = SetUpTest(log)
    prepare = PrepareTest()
    app = prepare.app
    root_app = prepare.root_app
    headers = {}

    @classmethod
    def setUpClass(cls) -> None:
        cls.headers["Authorization"] = cls.test.auth()
        cls.user = cls.test.get_user()
        cls.project = cls.test.create_project("invitation_testproject")
        cls.test.add_user_to_project(cls.user["id"], cls.project["id"], "admin")
        cls.emails = [ f"fakeunittest@email{i}.com" for i in range(4)]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.test.delete_project(cls.project["id"])
        for email in cls.emails:
            cls.test.delete_user_by_email(email)
        with cls.root_app.app_context():
            for email in cls.emails:
                invites = db.session.query(InvitationModel).filter_by(email=email)
                for invite in invites:
                    db.session.delete(invite)
            db.session.commit()

    @unittest.skip
    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_01_create_invitation(self, mock_email):
        payload = {
            "email": self.emails[0],
            "platform_role": "member",
            "ad_account_created": False,
            "relationship": {
                "project_geid": self.project["global_entity_id"],
                "project_role": "admin",
                "inviter": "admin",
            }
        }
        response = self.app.post("/v1/invitations", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        with self.root_app.app_context():
            invite = db.session.query(InvitationModel).filter_by(email=self.emails[0]).first()
        self.assertEqual(invite.email, self.emails[0])
        self.assertEqual(invite.project, str(self.project["id"]))

        response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/User/query", json={"email": self.emails[0]})
        user_node = response.json()[0]
        self.assertEqual(user_node["email"], self.emails[0])
        self.assertEqual(user_node["status"], "pending")
        self.assertEqual(user_node["role"], "member")

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_02_create_invitation_no_email(self, mock_email):
        payload = {
            "platform_role": "admin",
        }
        response = self.app.post("/v1/invitations", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["result"], "missing required field email")

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_03_create_invitation_member(self, mock_email):
        payload = {
            "email": self.emails[1],
            "platform_role": "member",
            "ad_account_created": False,
            "relationship": {
                "project_geid": self.project["global_entity_id"],
                "project_role": "admin",
                "inviter": "admin",
            }
        }
        headers = {}
        headers["Authorization"] = self.test.auth_member()
        response = self.app.post("/v1/invitations", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        with self.root_app.app_context():
            invite = db.session.query(InvitationModel).filter_by(email=self.emails[1]).first()
        self.assertEqual(invite.email, self.emails[1])
        self.assertEqual(invite.project, str(self.project["id"]))
        response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/User/query", json={"email": self.emails[1]})
        user_node = response.json()[0]
        self.assertEqual(user_node["email"], self.emails[1])
        self.assertEqual(user_node["status"], "pending")
        self.assertEqual(user_node["role"], "member")

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_04_create_invitation_no_relation(self, mock_email):
        payload = {
            "email": self.emails[2],
            "platform_role": "member",
            "ad_account_created": False,
            "relationship": {
                "project_geid": self.project["global_entity_id"],
                "project_role": "admin",
                "inviter": "admin",
            }
        }
        headers = {}
        self.test.remove_user_from_project(self.user["id"], self.project["id"])
        headers["Authorization"] = self.test.auth_member()

        response = self.app.post("/v1/invitations", json=payload, headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["result"], "Permission denied")

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_05_create_invitation_no_relation(self, mock_email):
        payload = {
            "email": self.emails[2],
            "platform_role": "admin",
            "ad_account_created": False,
        }
        response = self.app.post("/v1/invitations", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        with self.root_app.app_context():
            invite = db.session.query(InvitationModel).filter_by(email=self.emails[2]).first()
        self.assertEqual(invite.email, self.emails[2])
        self.assertEqual(invite.role, "admin")
        response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/User/query", json={"email": self.emails[2]})
        user_node = response.json()[0]
        self.assertEqual(user_node["email"], self.emails[2])
        self.assertEqual(user_node["status"], "pending")
        self.assertEqual(user_node["role"], "admin")

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_06_create_invitation_duplicate_user(self, mock_email):
        email = "jiayu.zhang015+10@gmail.com"
        payload = {
            "email": email,
            "platform_role": "admin",
            "ad_account_created": False,
        }
        response = self.app.post("/v1/invitations", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["result"], "[ERROR] User already exists in platform")

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_09_get_invite_list(self, mock_email):
        with self.root_app.app_context():
            invite = db.session.query(InvitationModel).filter_by(email=self.emails[0]).order_by(InvitationModel.expiry_timestamp.desc()).first()

        payload = {
            "page": 0,
            "page_size": 1,
            "filters": {
                "project_geid": self.project["global_entity_id"],
            }
        }
        response = self.app.post(f"/v1/invitation-list", headers=self.headers, json=payload)
        print(response.get_json()["result"])
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.get_json()["result"][0]["email"], invite.email)


    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_10_get_invite_list_memeber(self, mock_email):
        with self.root_app.app_context():
            invite = db.session.query(InvitationModel).filter_by(email=self.emails[0]).order_by(InvitationModel.expiry_timestamp.desc()).first()

        payload = {
            "page": 0,
            "page_size": 1,
            "filters": {
                "project_id": self.project["global_entity_id"],
            }
        }
        headers = {}
        headers["Authorization"] = self.test.auth_member()
        response = self.app.post(f"/v1/invitation-list", headers=headers, json=payload)
        self.assertEqual(response.status_code, 403)

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_11_create_invitation_missing_project_role(self, mock_email):
        payload = {
            "email": self.emails[0],
            "platform_role": "admin",
            "ad_account_created": False,
            "relationship": {
                "project_geid": self.project["global_entity_id"],
                "inviter": "test",
            }
        }
        response = self.app.post("/v1/invitations", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["result"], "missing required relation field project_role")

    def test_12_check_invite_email(self):
        payload = {
            "project_geid": self.project["global_entity_id"],
        }
        email = "jiayu.zhang015+10@gmail.com"
        response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/User/query", json={"email": email})
        user_node = response.json()[0]

        self.test.add_user_to_project(user_node["id"], self.project["id"], "admin")
        response = self.app.get("/v1/invitation/check/" + email, query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["email"], email)
        self.assertEqual(response.get_json()["result"]["relationship"]["project_code"], self.project["code"])
        self.test.remove_user_from_project(user_node["id"], self.project["id"])

    def test_13_check_invite_email_bad_geid(self):
        payload = {
            "project_geid": "invalid",
        }
        email = "jiayu.zhang015+10@gmail.com"
        response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/User/query", json={"email": email})
        user_node = response.json()[0]

        self.test.add_user_to_project(user_node["id"], self.project["id"], "admin")
        response = self.app.get("/v1/invitation/check/" + email, query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["result"], "Container does not exist in platform")
        self.test.remove_user_from_project(user_node["id"], self.project["id"])

    def test_14_check_invite_email_no_project(self):
        payload = {
        }
        email = "jiayu.zhang015+10@gmail.com"
        response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/User/query", json={"email": email})
        user_node = response.json()[0]

        response = self.app.get("/v1/invitation/check/" + email, query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["email"], email)
        self.assertEqual(response.get_json()["result"].get("relationship"), {})

    def test_15_check_invite_email_bad_user(self):
        payload = {
        }
        email = "fakeemailthatdoesnotexist@gmail.com"
        response = self.app.get("/v1/invitation/check/" + email, query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["result"]["msg"], "User does not exist in platform")

    def test_16_check_invite_email_member(self):
        payload = {
            "project_geid": self.project["global_entity_id"],
        }
        email = "jiayu.zhang015+10@gmail.com"
        response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/User/query", json={"email": email})
        user_node = response.json()[0]

        self.test.add_user_to_project(user_node["id"], self.project["id"], "admin")
        headers = {}
        headers["Authorization"] = self.test.auth_member()
        response = self.app.get("/v1/invitation/check/" + email, query_string=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["email"], email)
        self.assertEqual(response.get_json()["result"]["relationship"]["project_code"], self.project["code"])
        self.test.remove_user_from_project(user_node["id"], self.project["id"])

    def test_17_check_invite_bad_permission(self):
        payload = {
            "project_geid": self.project["global_entity_id"],
        }
        email = "jiayu.zhang015+10@gmail.com"
        headers = {}
        headers["Authorization"] = self.test.auth_member()
        response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/User/query", json={"email": email})
        user_node = response.json()[0]

        response = self.app.get("/v1/invitation/check/" + email, query_string=payload, headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["result"], "Permission denied")

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_18_create_invitation_member_not_in_project(self, mock_email):
        payload = {
            "email": self.emails[3],
            "platform_role": "member",
            "ad_account_created": False,
            "relationship": {
                "project_geid": self.project["global_entity_id"],
                "project_role": "admin",
                "inviter": "admin",
            }
        }
        headers = {}
        headers["Authorization"] = self.test.auth_member()
        response = self.app.post("/v1/invitations", json=payload, headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["result"], "Permission denied")

    def test_19_check_invite_permissions(self):
        payload = {
            "project_geid": self.project["global_entity_id"],
        }
        email = "jiayu.zhang015+10@gmail.com"
        headers = {}
        headers["Authorization"] = self.test.auth_member()
        response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/User/query", json={"email": email})
        user_node = response.json()[0]

        response = self.app.get("/v1/invitation/check/" + email, query_string=payload, headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["result"], "Permission denied")

    def test_20_check_invite_permissions_no_relation(self):
        payload = {
            "project_geid": self.project["global_entity_id"],
        }
        email = "jiayu.zhang015+10@gmail.com"

        response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/User/query", json={"email": email})
        user_node = response.json()[0]
        response = self.app.get("/v1/invitation/check/" + email, query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["relationship"], {})

    def test_21_get_invite_list_memeber_permission(self):
        with self.root_app.app_context():
            invite = db.session.query(InvitationModel).filter_by(email=self.emails[0]).order_by(InvitationModel.expiry_timestamp.desc()).first()

        payload = {
            "page": 0,
            "page_size": 1,
            "filters": {
                "project_id": self.project["global_entity_id"],
            }
        }
        headers = {}
        headers["Authorization"] = self.test.auth_member()
        self.test.add_user_to_project(self.user["id"], self.project["id"], "contributor")
        response = self.app.post(f"/v1/invitation-list", headers=headers, json=payload)
        self.assertEqual(response.status_code, 403)
