from app import create_app, create_db
from tests.logger import Logger
from config import ConfigClass
import requests
from resources.utils import fetch_geid
from models.api_resource_request import ResourceRequest, db


class SetUpTest:

    def __init__(self, log):
        self.log = log

    def auth(self, payload=None):
        if not payload:
            payload = {
                "username": "admin",
                "password": "admin",
                "realm": ConfigClass.KEYCLOAK_REALM
            }
        response = requests.post(ConfigClass.AUTH_SERVICE + "users/auth", json=payload)
        data = response.json()
        self.log.info(data)
        return data["result"].get("access_token")

    def auth_member(self, payload=None):
        if not payload:
            payload = {
                "username": "jzhang10",
                "password": ConfigClass.COLLAB_TEST_PASS,
                "realm": ConfigClass.KEYCLOAK_REALM
            }
        response = requests.post(ConfigClass.AUTH_SERVICE + "users/auth", json=payload)
        data = response.json()
        self.log.info(data)
        return data["result"].get("access_token")

    def get_user(self):
        payload = {
            "name": "jzhang10",
        }
        response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/User/query", json=payload)
        self.log.info(response.json())
        return response.json()[0]

    def get_user_by_name(self, username):
        payload = {
            "name": username,
        }
        response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/User/query", json=payload)
        self.log.info(response.json())
        return response.json()[0]
    
    def create_folder(self, geid, project_code, zone="greenroom", path="", name="bff_proxy_unittest_folder", parent_geid=""):
        self.log.info("\n")
        self.log.info("Creating testing folder".ljust(80, '-'))
        payload = {
            "global_entity_id": geid,
            "folder_name": name,
            "folder_level": 0,
            "uploader": "BFFUnittest",
            "folder_relative_path": path,
            "zone": zone,
            "project_code": project_code,
            "folder_tags": [],
            "folder_parent_geid": parent_geid,
            "folder_parent_name": "",
        }
        testing_api = 'folders'
        try:
            res = requests.post(ConfigClass.ENTITYINFO_SERVICE + testing_api, json=payload)
            self.log.info(f"RESPONSE DATA: {res.text}")
            self.log.info(f"RESPONSE STATUS: {res.status_code}")
            assert res.status_code == 200
            result = res.json().get('result')
            return result
        except Exception as e:
            self.log.info(f"ERROR CREATING FOLDER: {e}")
            raise e

    def create_project(self, code, discoverable='true'):
        self.log.info("\n")
        self.log.info("Preparing testing project".ljust(80, '-'))
        self.log.info("Project code: {}".format(code))
        testing_api = ConfigClass.NEO4J_SERVICE + "nodes/Container"
        params = {"name": "BFFProxyUnitTest",
                  "path": code,
                  "code": code,
                  "description": "Project created by unit test, will be deleted soon...",
                  "discoverable": discoverable,
                  "type": "Usecase",
                  "tags": ['test'],
                  "global_entity_id": fetch_geid("dataset") 
                  }
        self.log.info(f"POST API: {testing_api}")
        self.log.info(f"POST params: {params}")
        try:
            res = requests.post(testing_api, json=params)
            self.log.info(f"RESPONSE DATA: {res.text}")
            self.log.info(f"RESPONSE STATUS: {res.status_code}")
            assert res.status_code == 200
            return res.json() [0]
        except Exception as e:
            self.log.info(f"ERROR CREATING PROJECT: {e}")
            raise e

    def get_project(self, project_code):
        self.log.info("\n")
        self.log.info("Get project by project code".ljust(80, '-'))
        get_api = ConfigClass.NEO4J_SERVICE + "nodes/Container/query"
        payload = {
            "code": project_code
        }
        try:
            get_res = requests.post(get_api, json=payload)
            return get_res.json()[0]
        except Exception as e:
            self.log.info(f"ERROR GETTING PROJECT: {e}")
            raise e    

    def delete_project(self, node_id):
        self.log.info("\n")
        self.log.info("Preparing delete project".ljust(80, '-'))
        delete_api = ConfigClass.NEO4J_SERVICE + "nodes/Container/node/%s" % str(node_id)
        try:
            delete_res = requests.delete(delete_api)
            self.log.info(f"DELETE STATUS: {delete_res.status_code}")
            self.log.info(f"DELETE RESPONSE: {delete_res.text}")
        except Exception as e:
            self.log.info(f"ERROR DELETING PROJECT: {e}")
            self.log.info(f"PLEASE DELETE THE PROJECT MANUALLY WITH ID: {node_id}")
            raise e

    def add_user_to_project(self, user_id, project_id, role):
        payload = {
            "start_id": user_id,
            "end_id": project_id,
        }
        response = requests.post(ConfigClass.NEO4J_SERVICE + f"relations/{role}", json=payload)
        if response.status_code != 200:
            raise Exception(f"Error adding user to project: {response.json()}")

        response = requests.get(ConfigClass.NEO4J_SERVICE + f"nodes/User/node/{user_id}")
        if response.status_code != 200:
            raise Exception(f"Error geting user: {response.json()}")
        user_node = response.json()[0]

        response = requests.get(ConfigClass.NEO4J_SERVICE + f"nodes/Container/node/{project_id}")
        if response.status_code != 200:
            raise Exception(f"Error getting project: {response.json()}")
        project_node = response.json()[0]

        # Add role to keycloak
        try:
            payload = {
                "project_roles": ["admin", "contributor", "collaborator"],
                "project_code": project_node["code"],
                "realm": ConfigClass.KEYCLOAK_REALM,
            }
            response = requests.post(ConfigClass.AUTH_SERVICE + f"admin/users/realm-roles", json=payload)
            if response.status_code != 200:
                raise Exception(f"Error adding keycloak role: {response.json()}")
        except Exception as e:
            # Will except if the role already exists
            pass

        # Add keycloak role to user
        payload = {
            "email": user_node["email"],
            "realm": ConfigClass.KEYCLOAK_REALM,
        }
        # Add the correct role and remove the other project roles
        for project_role in ["admin", "contributor", "collaborator"]:
            payload["project_role"] = project_node["code"] + "-" + project_role
            if project_role == role:
                response = requests.post(ConfigClass.AUTH_SERVICE + f"user/project-role", json=payload)
            else:
                try:
                    response = requests.delete(ConfigClass.AUTH_SERVICE + f"user/project-role", json=payload)
                except Exception as e:
                    # will except if user doesn't have that role
                    continue
        if response.status_code != 200:
            raise Exception(f"Error adding keycloak role to user: {response.json()}")


    def remove_user_from_project(self, user_id, project_id):
        payload = {
            "start_id": user_id,
            "end_id": project_id,
        }
        response = requests.delete(ConfigClass.NEO4J_SERVICE + "relations", params=payload)
        if response.status_code != 200:
            raise Exception(f"Error removing user from project: {response.json()}")

        response = requests.get(ConfigClass.NEO4J_SERVICE + f"nodes/User/node/{user_id}")
        if response.status_code != 200:
            raise Exception(f"Error geting user: {response.json()}")
        user_node = response.json()[0]

        response = requests.get(ConfigClass.NEO4J_SERVICE + f"nodes/Container/node/{project_id}")
        if response.status_code != 200:
            raise Exception(f"Error getting project: {response.json()}")
        project_node = response.json()[0]

        # remove keycloak role from user
        payload = {
            "email": user_node["email"],
            "realm": ConfigClass.KEYCLOAK_REALM,
        }
        # Add the correct role and remove the other project roles
        for project_role in ["admin", "contributor", "collaborator"]:
            payload["project_role"] = project_node["code"] + "-" + project_role
            print(payload)
            print("***")
            try:
                response = requests.delete(ConfigClass.AUTH_SERVICE + f"user/project-role", json=payload)
            except Exception as e:
                print(str(e))
                # will except if user doesn't have that role
                continue
        if response.status_code != 200:
            raise Exception(f"Error adding keycloak role to user: {response.json()}")

    def remove_user_from_ad_group(self, user_email, project_code,headers):
        self.log.info("\n")
        self.log.info("Preparing removing user from ad group".ljust(80, '-'))
        payload = {
        "operation_type": "remove",
        "user_email": user_email,
        "group_code": project_code,
        }
        res = requests.put(
            url=ConfigClass.AUTH_SERVICE + "user/ad-group",
            json=payload,
            headers=headers
        )
        if(res.status_code != 200):
            raise Exception( f"Error removing user from group in ad: {res.text} {res.status_code}")


    def get_projects(self):
        all_project_url = ConfigClass.NEO4J_SERVICE + 'nodes/Container/properties'
        try:
            response = requests.get(all_project_url)
            if response.status_code == 200:
                res = response.json()
                projects = res.get('code')
                return projects
            else:
                self.log.error(f"RESPONSE ERROR: {response.text}")
                return None
        except Exception as e:
            raise e

    def delete_resource_requests(self, app, id):
        if id:
            app.delete(f"/v1/resource-requests/{id}/")
            
    def delete_folder_node(self, node_id):
        self.log.info("\n")
        self.log.info("Preparing delete folder node".ljust(80, '-'))
        delete_api = ConfigClass.NEO4J_SERVICE+ "nodes/Folder/node/%s" % str(node_id)
        try:
            delete_res = requests.delete(delete_api)
            self.log.info(f"DELETE STATUS: {delete_res.status_code}")
            self.log.info(f"DELETE RESPONSE: {delete_res.text}")
        except Exception as e:
            self.log.info(f"ERROR DELETING FILE: {e}")
            self.log.info(f"PLEASE DELETE THE FILE MANUALLY WITH ID: {node_id}")
            raise e

    def delete_user_by_email(self, email):
        self.log.info("\n")
        self.log.info("Preparing delete user node".ljust(80, '-'))

        response = requests.post(ConfigClass.NEO4J_SERVICE + "nodes/User/query", json={"email": email})
        if not response.json():
            return
        user_node = response.json()[0]
        delete_api = ConfigClass.NEO4J_SERVICE+ "nodes/User/node/%s" % str(user_node["id"])
        try:
            delete_res = requests.delete(delete_api)
            self.log.info(f"DELETE STATUS: {delete_res.status_code}")
            self.log.info(f"DELETE RESPONSE: {delete_res.text}")
        except Exception as e:
            self.log.info(f"ERROR DELETING FILE: {e}")
            self.log.info(f"PLEASE DELETE THE FILE MANUALLY WITH ID: {user_node['id']}")
            raise e


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class PrepareTest(metaclass=Singleton):

    def __init__(self):
        self.app, self.root_app  = self.create_test_client()

    def create_test_client(self):
        app = create_app()
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = ConfigClass.SQLALCHEMY_DATABASE_URI
        test_client = app.test_client(self)
        return test_client, app
