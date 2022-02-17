import json
import unittest
import requests
import time

class TestUser(unittest.TestCase):
    """This is the unit testing for user operation workflow.

    Testing cases:
        test 01-03: user register testings
        test 04: list all users in the platform

    """
    # Base URL
    base_url = "http://0.0.0.0:5060/v1"

    # Default testing user account
    new_user = {
        "name" : "testuser+%s"%int(time.time()*4),
        "first_name" : "test",
        "last_name" : "user",
        "password" : "12345"
    }

    def test_01_user_register(self):
        # Test case for registering user successfully
        res = requests.post(self.base_url+"/users", json=self.new_user)
        # print(res.text)
        self.assertEqual(res.status_code, 200)

    def test_02_user_register_duplicate(self):
        # Test case for registering duplicate user failed
        res = requests.post(self.base_url+"/users", json=self.new_user)
        self.assertEqual(res.status_code, 500)

    def test_03_user_register_insufficient(self):
        # Test case for registering with insufficient user information
        user_failed = self.new_user.copy()
        user_failed.pop("password", None)
        res = requests.post(self.base_url+"/users", json=user_failed)
        self.assertEqual(res.status_code, 400)

        result = json.loads(res.text)['result']
        self.assertEqual(result, 
            'missing username, password, first name or last name')
    
    def test_04_list_users_in_platform(self):
        # Test case for list all existed user in the platform
        # And check if the user just created exists
        res = requests.get(self.base_url+"/users")
        self.assertEqual(res.status_code, 200)

        result = json.loads(res.text)['result']
        user = [filter(lambda user: user['name'] == self.new_user.name, result)]
        self.assertEqual(len(user), 1) # Check if only one record matches


if __name__ == '__main__':
    unittest.main()


