import unittest
from tests.prepare_test import SetUpTest, PrepareTest
from tests.logger import Logger
from unittest import mock
from services.notifier_services.email_service import SrvEmail
import json
from config import ConfigClass


class TestFileMetaProxy(unittest.TestCase):
    log = Logger(name='test_api_file_v3_proxy.log')
    test = SetUpTest(log)
    app = PrepareTest().app
    headers = {}
    resource_requests = []

    @classmethod
    def setUpClass(cls) -> None:
        cls.headers["Authorization"] = cls.test.auth_member()
        cls.user = cls.test.get_user()
        cls.project = cls.test.create_project("file_meta_proxy_testproject")
        cls.project2 = cls.test.create_project("file_meta_proxy_testproject2")
        cls.project3 = cls.test.create_project("file_meta_proxy_testproject3")
        cls.project4 = cls.test.create_project("file_meta_proxy_testproject4")
        cls.test.add_user_to_project(cls.user["id"], cls.project["id"], "admin")
        cls.test.add_user_to_project(cls.user["id"], cls.project2["id"], "collaborator")
        cls.test.add_user_to_project(cls.user["id"], cls.project3["id"], "contributor")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.test.delete_project(cls.project["id"])
        cls.test.delete_project(cls.project2["id"])
        cls.test.delete_project(cls.project3["id"])
        cls.test.delete_project(cls.project4["id"])

    def test_01_dataset_file_query(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'source_type': 'Project',
            'zone': 'Greenroom',
            'project_geid': self.project["global_entity_id"],
        }
        geid = self.project["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_02_dataset_file_query_bad_zone(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'source_type': 'Project',
            'project_geid': self.project["global_entity_id"],
        }
        geid = self.project["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error_msg"], "Missing required paramter zone")

    def test_03_dataset_file_query_collaborator(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'source_type': 'Project',
            'zone': 'Greenroom',
            'project_geid': self.project2["global_entity_id"],
        }
        geid = self.project2["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_04_dataset_file_query_collaborator(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'Project',
            'zone': 'Greenroom',
            'project_geid': self.project2["global_entity_id"],
        }
        geid = self.project2["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_05_dataset_file_query_contributor(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'source_type': 'Project',
            'zone': 'Greenroom',
            'project_geid': self.project3["global_entity_id"],
        }
        geid = self.project3["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_06_dataset_file_query_contributor(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'Project',
            'zone': 'Greenroom',
            'project_geid': self.project3["global_entity_id"],
        }
        geid = self.project3["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_07_dataset_file_query_contributor_core(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'source_type': 'Project',
            'zone': ConfigClass.CORE_ZONE_LABEL,
            'project_geid': self.project3["global_entity_id"],
        }
        geid = self.project3["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error_msg"], "Permission Denied")

    #def test_08_dataset_file_query_contributor_wrong_user(self):
    #    payload = {
    #        'page': 0,
    #        'page_size': 10,
    #        'order_by': 'name',
    #        'order_type': 'desc',
    #        'query': '{"uploader": "jzhang11"}',
    #        'source_type': 'Project',
    #        'zone': 'Greenroom',
    #        'project_geid': self.project3["global_entity_id"],
    #    }
    #    geid = self.project3["global_entity_id"]
    #    response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
    #    self.assertEqual(response.status_code, 403)
    #    self.assertEqual(response.get_json()["error_msg"], "Permission Denied")

    def test_09_dataset_file_query_contributor_disable_fuzzy(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'partial': '["uploader"]',
            'source_type': 'Project',
            'zone': 'Greenroom',
            'project_geid': self.project3["global_entity_id"],
        }
        geid = self.project3["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_10_dataset_file_query_collaborator_greenroom(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'Project',
            'zone': 'Greenroom',
            'project_geid': self.project3["global_entity_id"],
        }
        geid = self.project3["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    #def test_11_dataset_file_query_collaborator_greenroom_wrong_user(self):
    #    payload = {
    #        'page': 0,
    #        'page_size': 10,
    #        'order_by': 'name',
    #        'order_type': 'desc',
    #        'query': '{"uploader": "jzhang11"}',
    #        'source_type': 'Project',
    #        'zone': 'Greenroom',
    #        'project_geid': self.project2["global_entity_id"],
    #    }
    #    geid = self.project2["global_entity_id"]
    #    response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
    #    self.assertEqual(response.status_code, 403)
    #    self.assertEqual(response.get_json()["error_msg"], "Permission Denied")

    def test_12_dataset_file_query_collaborator_greenroom_fuzzy_user(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'partial': '["name"]',
            'source_type': 'Project',
            'zone': 'Greenroom',
            'project_geid': self.project2["global_entity_id"],
        }
        geid = self.project2["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_13_dataset_file_query_bad_geid(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'source_type': 'Project',
            'zone': 'Greenroom',
            'project_geid': 'bad',
        }
        response = self.app.get("/v1/files/entity/meta/bad", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error_msg"], "Container not found")

    def test_14_dataset_file_query_not_memeber(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'source_type': 'Project',
            'zone': 'Greenroom',
            'project_geid': self.project4["global_entity_id"],
        }
        geid = self.project4["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error_msg"], "Permission Denied")

@unittest.skip("need update")
class TestFolderFileProxy(unittest.TestCase):
    log = Logger(name='test_api_file_meta_proxy.log')
    test = SetUpTest(log)
    app = PrepareTest().app
    headers = {}
    resource_requests = []

    @classmethod
    def setUpClass(cls) -> None:
        cls.headers["Authorization"] = cls.test.auth_member()
        cls.user = cls.test.get_user()
        cls.project = cls.test.create_project("file_meta_testproject")
        cls.project2 = cls.test.create_project("file_meta_testproject2")
        cls.project3 = cls.test.create_project("file_meta_testproject3")
        cls.project4 = cls.test.create_project("file_meta_testproject4")
        cls.test.add_user_to_project(cls.user["id"], cls.project["id"], "admin")
        cls.test.add_user_to_project(cls.user["id"], cls.project2["id"], "collaborator")
        cls.test.add_user_to_project(cls.user["id"], cls.project3["id"], "contributor")
        cls.test.add_user_to_project(cls.user["id"], cls.project4["id"], "contributor")
        cls.folder_root_1 = cls.test.create_folder(
            "unit_test_folder_1_root", 
            cls.project["code"], 
            name=cls.user["username"]
        )
        cls.folder_1 = cls.test.create_folder(
            "unit_test_folder_1", 
            cls.project["code"], 
            path=cls.user["username"], 
            parent_geid=cls.folder_root_1["global_entity_id"]
        )
        cls.folder_root_2 = cls.test.create_folder(
            "unit_test_folder_2_root", 
            cls.project2["code"], 
            name=cls.user["username"],
        )
        cls.folder_2 = cls.test.create_folder(
            "unit_test_folder_2", 
            cls.project2["code"], 
            path=cls.user["username"],
            parent_geid=cls.folder_root_2["global_entity_id"]
        )
        cls.folder_root_3 = cls.test.create_folder(
            "unit_test_folder_3_root", 
            cls.project3["code"], 
            name=cls.user["username"]
        )
        cls.folder_3 = cls.test.create_folder(
            "unit_test_folder_3", 
            cls.project3["code"], 
            path=cls.user["username"],
            parent_geid=cls.folder_root_3["global_entity_id"]
        )
        cls.folder_3_core = cls.test.create_folder(
            "unit_test_folder_3_core", 
            cls.project3["code"], 
            zone="core", 
            path=cls.user["username"],
            parent_geid=cls.folder_root_3["global_entity_id"],
        )
        cls.folder_root_4 = cls.test.create_folder(
            "unit_test_folder_4_root", 
            cls.project3["code"], 
            name="gregmccoy"
        )
        cls.folder_4 = cls.test.create_folder(
            "unit_test_folder_4", 
            cls.project3["code"], 
            path="gregmccoy",
            parent_geid=cls.folder_root_4["global_entity_id"]
        )
        cls.folder_root_5 = cls.test.create_folder(
            "unit_test_folder_5_root", 
            cls.project2["code"], 
            name="gregmccoy"
        )
        cls.folder_5 = cls.test.create_folder(
            "unit_test_folder_5", 
            cls.project2["code"], 
            path="gregmccoy",
            parent_geid=cls.folder_root_5["global_entity_id"]
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.test.delete_project(cls.project["id"])
        cls.test.delete_project(cls.project2["id"])
        cls.test.delete_project(cls.project3["id"])
        cls.test.delete_project(cls.project4["id"])

        cls.test.delete_folder_node(cls.folder_1["id"])
        cls.test.delete_folder_node(cls.folder_2["id"])
        cls.test.delete_folder_node(cls.folder_3["id"])
        cls.test.delete_folder_node(cls.folder_4["id"])
        cls.test.delete_folder_node(cls.folder_5["id"])
        cls.test.delete_folder_node(cls.folder_3_core["id"])
        cls.test.delete_folder_node(cls.folder_root_1["id"])
        cls.test.delete_folder_node(cls.folder_root_2["id"])
        cls.test.delete_folder_node(cls.folder_root_3["id"])
        cls.test.delete_folder_node(cls.folder_root_4["id"])
        cls.test.delete_folder_node(cls.folder_root_5["id"])

    def test_01_dataset_file_query(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'source_type': 'Folder',
            'zone': 'All',
            'project_geid': self.project["global_entity_id"]
        }
        geid = self.folder_1["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_02_dataset_file_query_missing_zone(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'source_type': 'Folder',
            'project_geid': self.project["global_entity_id"]
        }
        geid = self.folder_1["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error_msg"], "Missing required paramter zone")

    def test_03_dataset_file_query(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'Folder',
            'zone': 'All',
            'project_geid': self.project["global_entity_id"],
        }
        geid = self.folder_1["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_04_dataset_file_query_contributor(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'source_type': 'Folder',
            'zone': 'Greenroom',
            'project_geid': self.project3["global_entity_id"],
        }
        geid = self.folder_3["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_05_dataset_file_query_contributor_missing_uploader(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'Folder',
            'zone': 'All',
            'project_geid': self.project3["global_entity_id"],
        }
        geid = self.folder_3_core["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error_msg"], "Permission Denied")

    def test_06_dataset_file_query_contributor_wrong_user(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'Folder',
            'zone': 'All',
            'project_geid': self.project3["global_entity_id"],
        }
        geid = self.folder_4["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error_msg"], "Permission Denied")

    def test_07_dataset_file_query_contributor_core(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'source_type': 'Folder',
            'zone': ConfigClass.CORE_ZONE_LABEL,
            'project_geid': self.project3["global_entity_id"],
        }
        geid = self.folder_3_core["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error_msg"], "Permission Denied")

    def test_08_dataset_file_query_contributor_uploader(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'partial': '["name"]',
            'source_type': 'Folder',
            'zone': 'Greenroom',
            'project_geid': self.project3["global_entity_id"],
        }
        geid = self.folder_3["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_09_dataset_file_query_collaboratorr_uploader(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'partial': '["name"]',
            'source_type': 'Folder',
            'zone': 'All',
            'project_geid': self.project2["global_entity_id"],
        }
        geid = self.folder_2["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_09_dataset_file_query_collaborator_uploader_missing(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'Folder',
            'zone': 'All',
            'project_geid': self.project2["global_entity_id"],
        }
        geid = self.folder_2["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_10_dataset_file_query_collaboratorr_uploader_wrong(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'Folder',
            'zone': 'All',
            'project_geid': self.project2["global_entity_id"],
        }
        geid = self.folder_5["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error_msg"], "Permission Denied")

    def test_11_dataset_file_query_collaboratorr_uploader_fuzzy(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'partial': '["name"]',
            'source_type': 'Folder',
            'zone': 'Greenroom',
            'project_geid': self.project2["global_entity_id"],
        }
        geid = self.folder_2["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"], [])

    def test_12_dataset_file_query_missing_source(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'partial': '["name"]',
            'zone': 'Greenroom',
            'project_geid': self.project2["global_entity_id"],
        }
        geid = self.folder_2["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error_msg"], "Missing required paramter source_type")

    def test_13_dataset_file_query_missing_source(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': 'bad json',
            'partial': '["name"]',
            'source_type': 'Folder',
            'zone': 'Greenroom',
            'project_geid': self.project2["global_entity_id"],
        }
        geid = self.folder_2["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error_msg"], "Invalid query json")

    def test_14_dataset_file_query_missing_source(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'partial': 'bad json',
            'source_type': 'Folder',
            'zone': 'Greenroom',
            'project_geid': self.project2["global_entity_id"],
        }
        geid = self.folder_2["global_entity_id"]
        response = self.app.get(f"/v1/files/entity/meta/{geid}", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error_msg"], "Invalid partial json")

    def test_15_dataset_file_query_bad_geid(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{"uploader": "jzhang10"}',
            'source_type': 'Folder',
            'zone': 'Greenroom',
            'project_geid': self.project2["global_entity_id"],
        }
        response = self.app.get("/v1/files/entity/meta/bad", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error_msg"], "Folder not found")

    def test_16_home_meta_not_found(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'Folder',
            'zone': 'Greenroom',
            'project_geid': self.project4["global_entity_id"]
        }
        response = self.app.get("/v1/files/entity/meta/", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["result"], "Home Folder not found")

    def test_17_home_meta(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'Folder',
            'zone': 'Greenroom',
            'project_geid': self.project3["global_entity_id"]
        }
        response = self.app.get("/v1/files/entity/meta/", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"]["data"][0]["name"], "bff_proxy_unittest_folder")

    def test_18_home_meta_dataset_not_found(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'Folder',
            'zone': 'Greenroom',
            'project_geid': 'invalid'
        }
        response = self.app.get("/v1/files/entity/meta/", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error_msg"], "Dataset not found")

    def test_19_home_meta_invalid_zone(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'Folder',
            'zone': 'invalid',
            'project_geid': self.project3["global_entity_id"]
        }
        response = self.app.get("/v1/files/entity/meta/", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error_msg"], "Invalid zone")

    def test_20_home_meta_invalid_zone(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'invalid',
            'zone': 'Greenroom',
            'project_geid': self.project3["global_entity_id"]
        }
        response = self.app.get("/v1/files/entity/meta/", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error_msg"], "Invalid source_type")

    def test_21_home_meta_invalid_zone(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'query': '{',
            'source_type': 'Folder',
            'zone': 'Greenroom',
            'project_geid': self.project3["global_entity_id"]
        }
        response = self.app.get("/v1/files/entity/meta/", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error_msg"], "Invalid query json")

    def test_22_home_meta_no_permissions(self):
        payload = {
            'page': 0,
            'page_size': 10,
            'order_by': 'name',
            'order_type': 'desc',
            'source_type': 'Folder',
            'zone': ConfigClass.CORE_ZONE_LABEL,
            'project_geid': self.project3["global_entity_id"]
        }
        response = self.app.get("/v1/files/entity/meta/", query_string=payload, headers=self.headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error_msg"], "Permission Denied")
