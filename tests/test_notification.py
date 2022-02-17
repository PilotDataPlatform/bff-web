import unittest
import pytest
from tests.prepare_test import SetUpTest, PrepareTest
from tests.logger import Logger
from config import ConfigClass


class TestNotification(unittest.TestCase):
    log = Logger(name='test_notification.log')
    test = SetUpTest(log)
    app = PrepareTest().app
    admin_headers = {}
    not_admin_headers = {}
    project = None

    @classmethod
    def setUpClass(cls) -> None:
        admin_payload = {
            "username": "admin",
            "password": "admin",
            "realm": ConfigClass.KEYCLOAK_REALM
        }
        not_admin_payload = {
            "username": "kaiyaozhang9200",
            "password": "indoc101!",
            "realm": ConfigClass.KEYCLOAK_REALM
        }
        cls.admin_headers["Authorization"] = cls.test.auth_member(admin_payload)
        cls.not_admin_headers["Authorization"] = cls.test.auth_member(not_admin_payload)
        cls.project = cls.test.create_project("notification_test")
        cls.project_geid = cls.project["global_entity_id"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.test.delete_project(cls.project["id"])
    
    @pytest.mark.skip()
    def test_01_get_notification(self):
        self.log.info("Test case 1: Get notification with id=1")
        response = self.app.get("/v1/notification?id=1", headers=self.admin_headers)
        self.log.info(f"Response payload: {response}")
        self.assertEqual(response.status_code, 200)

    @pytest.mark.skip()
    def test_02_post_notification(self):
        self.log.info("Test case 2: Post notification")
        payload = {
            'type': 'test_02',
            'message': 'Test message from post',
            'detail': {
                'maintenance_date': '2022-01-20T15:20:13.955Z',
                'duration': 1,
                'duration_unit': 'h'
            }
        }
        response = self.app.post('/v1/notification', json=payload, headers=self.admin_headers)
        self.log.info(f"Response payload: {response}")
        self.assertEqual(response.status_code, 200)

    @pytest.mark.skip()
    def test_03_put_notification(self):
        self.log.info("Test case 3: Put notification with id=1")
        payload = {
            'type': 'test_03',
            'message': 'Test message from put',
            'detail': {
                'maintenance_date': '2022-01-20T15:20:13.955Z',
                'duration': 1,
                'duration_unit': 'h'
            }
        }
        response = self.app.put('/v1/notification?id=1', json=payload, headers=self.admin_headers)
        self.log.info(f"Response payload: {response}")
        self.assertEqual(response.status_code, 200)

    @pytest.mark.skip()
    def test_04_delete_notification(self):
        self.log.info("Test case 4: Delete notification with id=1")
        response = self.app.delete('/v1/notification?id=1', headers=self.admin_headers)
        self.log.info(f"Response payload: {response}")
        self.assertEqual(response.status_code, 200)

    @pytest.mark.skip()
    def test_05_get_notifications(self):
        self.log.info("Test case 5: Get many notifications")
        response = self.app.get("/v1/notifications", headers=self.admin_headers)
        self.log.info(f"Response payload: {response}")
        self.assertEqual(response.status_code, 200)

    @pytest.mark.skip()
    def test_06_unsubscribe(self):
        self.log.info("Test case 6: Unsubscribe from notification with id=1")
        payload = {
            'username': 'erik',
            'notification_id': 1,
        }
        response = self.app.post("/v1/unsubscribe", json=payload, headers=self.admin_headers)
        self.log.info(f"Response payload: {response}")
        self.assertEqual(response.status_code, 200)
