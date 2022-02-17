import json
import unittest
import requests
import time
import uuid

class TestEmailSrv(unittest.TestCase):
    def test_01_send(self):
        url = "http://10.3.9.240:5065/v1/email"
        payload = {
            "sender": "notification@test",
            "receiver": "kang.huang.ut+111@gmail.com",
            "message": "You've been invited to a new PROJECT:  http://10.3.9.240:5065/v1/emai"
        }
        res = requests.post(
            url=url,
            json=payload
        )
        print(res.text)
        self.assertEqual(res.status_code, 200)

if __name__ == '__main__':
    unittest.main()
