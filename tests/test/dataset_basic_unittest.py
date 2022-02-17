import json
import unittest
import requests
import time
import uuid

class TestDataset(unittest.TestCase):
    """This is the unit testing for dataset operation workflow.

    Testing cases:
        test 01-02: dataset register testings
        test 03: list all datasets in the platform
        test 04: query datasets

    """

    # Base URL
    # base_url = "http://0.0.0.0:6061/v1" # PILOT
    base_url = "http://0.0.0.0:5060/v1" 


    # generate the test dataset infomation
    payload = {}
    uuid = str(uuid.uuid4())
    dataset_name = "test_dataset_%s"%(uuid)
    payload.update({"dataset_name": dataset_name})

    # generate random metadata format
    metadatas = {}
    for x in range(0, 5):
        metadatas.update({'metas_%d'%(x): "meta_val_%d"%(x)})

    payload.update({"metadatas": metadatas})

    # now add the child/parent tree
    child_dataset_name = "test_child_dataset_%s"%(uuid)
    gchild_dataset_name = "test_grand_child_dataset_%s"%(uuid)
    parent_dataset_name = "test_parent_dataset_%s"%(uuid)
    gparent_dataset_name = "test_grand_parent_dataset_%s"%(uuid)

    print("###### TEST CASE: TestDataset")
    print("dataset_name:", dataset_name)
    print("child_dataset_name:", child_dataset_name)
    print("gchild_dataset_name:", gchild_dataset_name)
    print("parent_dataset_name:", parent_dataset_name)
    print("gparent_dataset_name:", gparent_dataset_name)

    # Query payload
    query_payload = {
        "name": "test_dataset",
        "metadatas": {
            "metas_0": [
                "meta_val_0"
            ]
        },
        "time_lastmodified": [
            "2020-06-01T21:23:01.503Z",
            "2022-06-20T21:23:01.503Z"
        ],
        "time_created": [
            "2020-06-01T21:23:01.503Z",
            "2022-06-20T21:23:01.503Z"
        ]
    }

    def test_01_dataset_register(self):
        res = requests.post(self.base_url+"/datasets", json=self.payload)
        print(res.text)
        queried_dataset = json.loads(res.text)['result']
        self.__class__.dataset_id = queried_dataset['id']
        self.assertEqual(res.status_code, 200)

        # then query to see if it is there
        res = requests.post(self.base_url+"/datasets/queries", json={"name":self.dataset_name})
        self.assertEqual(queried_dataset['name'], self.dataset_name)
        

    # # block it if we have the duplicate name
    # def test_02_dataset_register_duplicate(self):
    #     res = requests.post(self.base_url+"/datasets", json=self.payload)
    #     self.assertEqual(res.status_code, 403)

    # test is to add the parent when create the dataset
    def test_03_parent_in_register(self):
        res = requests.post(self.base_url+"/datasets", 
            json={"dataset_name": self.child_dataset_name, "parent_id": self.dataset_id})
        queried_dataset = json.loads(res.text)['result']
        print(queried_dataset)
        self.__class__.child_dataset_id = queried_dataset['id']
        self.assertEqual(res.status_code, 200)

        # then check if dataset has one child
        res = requests.get(self.base_url+"/datasets/%s/relations/children"%self.dataset_id)
        self.assertEqual(queried_dataset['name'], self.child_dataset_name)

    def test_04_dataset_list(self):
        # list all datasets in the platform
        res = requests.get(self.base_url+"/datasets")
        self.assertEqual(res.status_code, 200)

    def test_05_dataset_query(self):
        # Test case for registering dataset
        res = requests.post(self.base_url+"/datasets/queries", json=self.query_payload)
        self.assertEqual(res.status_code, 200)

        result = json.loads(res.text)['result']
        self.assertGreaterEqual(len(result), 1) # Check if only one record matches

    def test_06_dataset_add_user(self):
        # registering a user in the dataset as member
        role = {
            "role":"member"
        }
        res = requests.post(self.base_url + "/datasets/" + 
                str(self.__class__.dataset_id) + "/users/admin", json=role)
        self.assertEqual(res.status_code, 200)
        

    def test_07_dataset_update_permission(self):
        # update user's permission to admin
        role = {
            "role":"admin"
        }
        res = requests.put(self.base_url + "/datasets/" + 
                str(self.__class__.dataset_id) + "/users/admin", json=role)
        self.assertEqual(res.status_code, 200)

    # test to add the child with grand child to it
    def test_08_dataset_add_childs(self):
        # create the grand child
        res = requests.post(self.base_url+"/datasets", 
            json={"dataset_name": self.gchild_dataset_name})
        queried_dataset = json.loads(res.text)['result']
        self.__class__.grand_child_dataset_id = queried_dataset['id']
        self.assertEqual(res.status_code, 200)

        # add the grand child to child
        res = requests.post(self.base_url+"/datasets/%s/relations/children"%self.child_dataset_id, 
            json={"target_dataset": self.grand_child_dataset_id})
        self.assertEqual(res.status_code, 200)

        # # then check if dataset has one child
        # res = requests.get(self.base_url+"/datasets/%s/relations/children"%self.child_dataset_id)
        # # print(json.loads(res.text))
        # queried_dataset = json.loads(res.text)['result'][0]
        # self.assertEqual(queried_dataset['id'], self.grand_child_dataset_id)

    def test_08_add_parent_gparent(self):
        # create the gparent
        res = requests.post(self.base_url+"/datasets", 
            json={"dataset_name": self.parent_dataset_name})
        queried_dataset = json.loads(res.text)['result']
        self.__class__.parent_dataset_id = queried_dataset['id']
        self.assertEqual(res.status_code, 200)

        # add the grand child to child
        res = requests.post(self.base_url+"/datasets/%s/relations/parent"%self.dataset_id, 
            json={"target_dataset": self.parent_dataset_id})
        self.assertEqual(res.status_code, 200)

        # then check if dataset has one child
        res = requests.get(self.base_url+"/datasets/%s/relations/parent"%self.dataset_id)
        # print(json.loads(res.text))
        queried_dataset = json.loads(res.text)['result'][0]
        self.assertEqual(queried_dataset['id'], self.parent_dataset_id)

        # ###################################### grand parent ####################################
        # create the parent
        res = requests.post(self.base_url+"/datasets", 
            json={"dataset_name": self.gparent_dataset_name})
        queried_dataset = json.loads(res.text)['result']
        # print(queried_dataset)
        self.__class__.grand_parent_dataset_id = queried_dataset['id']
        self.assertEqual(res.status_code, 200)

        # add the grand child to child
        res = requests.post(self.base_url+"/datasets/%s/relations/parent"%self.parent_dataset_id, 
            json={"target_dataset": self.grand_parent_dataset_id})
        self.assertEqual(res.status_code, 200)

        # then check if dataset has one child
        res = requests.get(self.base_url+"/datasets/%s/relations/parent"%self.parent_dataset_id)
        queried_dataset = json.loads(res.text)['result'][0]
        self.assertEqual(queried_dataset['id'], self.grand_parent_dataset_id)


    def test_09_parent_child_add_self(self):
        # add the grand child to child
        res = requests.post(self.base_url+"/datasets/%s/relations/parent"%self.dataset_id, 
            json={"target_dataset": self.dataset_id})
        self.assertEqual(res.status_code, 403)

        # add the grand child to child
        res = requests.post(self.base_url+"/datasets/%s/relations/children"%self.dataset_id, 
            json={"target_dataset": self.dataset_id})
        self.assertEqual(res.status_code, 403)


    def test_10_parent_child_cycle_prevent(self):
        # add the grand child as parent
        res = requests.post(self.base_url+"/datasets/%s/relations/parent"%self.dataset_id, 
            json={"target_dataset": self.grand_child_dataset_id})
        self.assertEqual(res.status_code, 403)

        # add the grand prarent as child
        print(self.dataset_id, self.grand_parent_dataset_id)
        res = requests.post(self.base_url+"/datasets/%s/relations/children"%self.dataset_id, 
            json={"target_dataset": self.grand_parent_dataset_id})
        self.assertEqual(res.status_code, 403)

    def test_11_parent_child_duplicate_add(self):
        # add the grand parent again
        res = requests.post(self.base_url+"/datasets/%s/relations/parent"%self.parent_dataset_id, 
            json={"target_dataset": self.grand_parent_dataset_id})
        self.assertEqual(res.status_code, 403)

        # add the grand child again
        res = requests.post(self.base_url+"/datasets/%s/relations/children"%self.child_dataset_id, 
            json={"target_dataset": self.grand_child_dataset_id})
        self.assertEqual(res.status_code, 403)


    # def test_32767_self_destruction(self):
    #     pass

if __name__ == '__main__':
    unittest.main()
