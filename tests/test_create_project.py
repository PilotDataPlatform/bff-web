import unittest
from tests.prepare_test import SetUpTest, PrepareTest
from tests.logger import Logger
from config import ConfigClass


class TestCreateProject(unittest.TestCase):
    log = Logger(name='test_create_project_api.log')
    test = SetUpTest(log)
    app = PrepareTest().app
    headers = {}

    @classmethod
    def setUpClass(cls) -> None:
        payload = {
            "username": "admin",
            "password": "admin",
            "realm": ConfigClass.KEYCLOAK_REALM,
        }
        cls.headers["Authorization"] = cls.test.auth_member(payload)
    
    def test_01_create_project(self):
        self.log.info("test case 1: Create project with wrong project name ")
        payload = {
            "name": "bjhogz6430p1a3!qwhx12lfwirgfxvx2bjhogz6430p1a3!qwhx12lfwirgfxvx2bjhogz6430p1a3!qwhx12lfwirgfxvx212341",
            "code": "a12",
            "discoverable": True,
            "type": "project",
            "icon": ""
        }
        response = self.app.post(f"v1/projects", headers=self.headers, json = payload)
        self.log.info(f"Response payload: {response}")
        res = response.json
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res["error_msg"], "Project name does not match the pattern.")

    def test_02_create_project(self):
        self.log.info("test case 2: Create project without project name")
        payload = {
            "name": "",
            "code": "a123",
            "discoverable": True,
            "type": "project",
            "icon": ""
        }
        response = self.app.post(f"v1/projects", headers=self.headers, json = payload)
        self.log.info(f"Response payload: {response}")
        res = response.json
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res["error_msg"], "Error the name and code field is required")

    def test_03_create_project(self):
        self.log.info("test case 3: Create project with project code >32")
        payload = {
            "name": "Test project",
            "code": "bjhogz6430p1abjhogz6430p1abjhogz6",
            "discoverable": True,
            "type": "project",
            "icon": ""
        }
        response = self.app.post(f"v1/projects", headers=self.headers, json = payload)
        self.log.info(f"Response payload: {response}")
        res = response.json
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res["error_msg"], "Project code does not match the pattern.")

    def test_04_create_project(self):
        self.log.info("test case 4: Create project with project code not start with letter")
        payload = {
            "name": "Test project",
            "code": "1bjh",
            "discoverable": True,
            "type": "project",
            "icon": ""
        }
        response = self.app.post(f"v1/projects", headers=self.headers, json = payload)
        self.log.info(f"Response payload: {response}")
        res = response.json
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res["error_msg"], "Project code does not match the pattern.")
    
    def test_05_create_project(self):
        self.log.info("test case 5: Create project with project code with special characters")
        payload = {
            "name": "Test project",
            "code": "1bjh!@#",
            "discoverable": True,
            "type": "project",
            "icon": ""
        }
        response = self.app.post(f"v1/projects", headers=self.headers, json = payload)
        self.log.info(f"Response payload: {response}")
        res = response.json
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res["error_msg"], "Project code does not match the pattern.")
    
    def test_06_create_project(self):
        self.log.info("test case 6: Create project without project code")
        payload = {
            "name": "Test project",
            "code": "",
            "discoverable": True,
            "type": "project",
            "icon": ""
        }
        response = self.app.post(f"v1/projects", headers=self.headers, json = payload)
        self.log.info(f"Response payload: {response}")
        res = response.json
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res["error_msg"], "Error the name and code field is required")
    
    def test_07_create_project(self):
        self.log.info("test case 7: Create project with duplicate project code")
        payload = {
            "name": "Test project",
            "code": "cli",
            "discoverable": True,
            "type": "project",
            "icon": ""
        }
        response = self.app.post(f"v1/projects", headers=self.headers, json = payload)
        self.log.info(f"Response payload: {response}")
        res = response.json
        self.assertEqual(response.status_code, 409)
        self.assertEqual(res["error_msg"], "Error duplicate project code")
    
