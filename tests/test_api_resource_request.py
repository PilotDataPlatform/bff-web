import unittest
from tests.prepare_test import SetUpTest, PrepareTest
from tests.logger import Logger
from unittest import mock
from services.notifier_services.email_service import SrvEmail
import json


class TestResourceRequestAPI(unittest.TestCase):
    project2 , project= None, None
    log = Logger(name='test_api_resource_request.log')
    test = SetUpTest(log)
    app = PrepareTest().app
    headers = {}
    resource_requests = []

    @classmethod
    def setUpClass(cls) -> None:
        cls.headers["Authorization"] = cls.test.auth()
        cls.user = cls.test.get_user()
        cls.project = cls.test.create_project("resource_request_testproject")
        cls.project2 = cls.test.create_project("resource_request_testproject2")
        cls.test.add_user_to_project(cls.user["id"], cls.project["id"], "admin")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.test.delete_project(cls.project["id"])
        cls.test.delete_project(cls.project2["id"])
        for resource in cls.resource_requests:
            cls.test.delete_resource_requests(cls.app, resource)

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_01_create_resource_request(self, mock_email):
        payload = {
            "user_geid": self.user["global_entity_id"],
            "project_geid": self.project["global_entity_id"],
            "request_for": "SuperSet",
        }
        headers = {"Authorization": self.test.auth_member()}
        response = self.app.post("/v1/resource-requests", json=payload, headers=headers)
        self.resource_requests.append(response.get_json()["result"]["id"])
        self.assertEqual(response.status_code, 200)

    def test_02_resource_request_query(self):
        payload = {
            "filters": {
                "project_geid": self.project["global_entity_id"]
            }
        }
        headers = {"Authorization": self.test.auth()}
        response = self.app.post("/v1/resource-requests/query", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()["result"][0]
        self.assertEqual(data["user_geid"], self.user["global_entity_id"])
        self.assertEqual(data["project_name"], self.project["name"])
        self.assertEqual(data["request_for"], "SuperSet")
        self.assertEqual(data["active"], True)

    def test_03_resource_request_get_single(self):
        headers = {"Authorization": self.test.auth()}
        id = self.resource_requests[0]
        response = self.app.get(f"/v1/resource-request/{id}/", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()["result"]
        self.assertEqual(data["user_geid"], self.user["global_entity_id"])
        self.assertEqual(data["project_name"], self.project["name"])
        self.assertEqual(data["request_for"], "SuperSet")

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_04_put_resource_request(self, mock_email):
        headers = {"Authorization": self.test.auth()}
        id = self.resource_requests[0]
        response = self.app.put(f"/v1/resource-request/{id}/complete", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()["result"]
        self.assertEqual(data["active"], False)
        self.assertEqual(data["project_name"], self.project["name"])
        self.assertEqual(data["request_for"], "SuperSet")

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_05_create_resource_request_missing(self, mock_email):
        payload = {
            "project_geid": self.project["global_entity_id"],
            "request_for": "SuperSet",
        }
        headers = {"Authorization": self.test.auth_member()}
        response = self.app.post("/v1/resource-requests", json=payload, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertTrue("Missing required field" in response.get_json()["result"])

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_07_create_resource_request_bad_resource(self, mock_email):
        payload = {
            "user_geid": self.user["global_entity_id"],
            "project_geid": self.project["global_entity_id"],
            "request_for": "SuperSet2",
        }
        headers = {"Authorization": self.test.auth_member()}
        response = self.app.post("/v1/resource-requests", json=payload, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertTrue("Invalid request_for field" in response.get_json()["result"])

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_08_create_resource_request_user_not_found(self, mock_email):
        payload = {
            "user_geid": "invalid",
            "project_geid": self.project["global_entity_id"],
            "request_for": "SuperSet",
        }
        headers = {"Authorization": self.test.auth_member()}
        response = self.app.post("/v1/resource-requests", json=payload, headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertTrue("User not found in neo4j" in response.get_json()["result"])

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_09_create_resource_request_permission(self, mock_email):
        payload = {
            "user_geid": self.user["global_entity_id"],
            "project_geid": self.project2["global_entity_id"],
            "request_for": "SuperSet",
        }
        headers = {"Authorization": self.test.auth_member()}
        response = self.app.post("/v1/resource-requests", json=payload, headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertTrue("Permission Denied" in response.get_json()["result"])

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    @unittest.skip("need update")
    def test_10_create_resource_guacomole(self, mock_email):
        payload = {
            "user_geid": self.user["global_entity_id"],
            "project_geid": self.project["global_entity_id"],
            "request_for": "Guacamole",
        }
        headers = {"Authorization": self.test.auth_member()}
        response = self.app.post("/v1/resource-requests", json=payload, headers=headers)
        self.resource_requests.append(response.get_json()["result"]["id"])
        self.assertEqual(response.status_code, 200)

    @unittest.skip("need update")
    def test_11_resource_request_query(self):
        payload = {
            "page": 0,
            "page_size": 1,
            "filters": {
                "project_geid": self.project["global_entity_id"]
            },
            "order_by": "request_date",
            "order_type": "desc",
        }
        headers = {"Authorization": self.test.auth()}
        response = self.app.post("/v1/resource-requests/query", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()["result"][0]
        self.assertEqual(data["request_for"], "SuperSet")
        self.assertEqual(data["active"], True)
        self.assertEqual(response.get_json()["total"], 2)

    @mock.patch.object(SrvEmail, 'send', side_effect=None)
    def test_12_put_resource_request_member(self, mock_email):
        headers = {"Authorization": self.test.auth_member()}
        id = self.resource_requests[0]
        response = self.app.put(f"/v1/resource-request/{id}/complete", headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertTrue("Permission Denied" in response.get_json()["error_msg"])

