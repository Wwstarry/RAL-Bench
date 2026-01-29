import unittest
import requests
import json
import time

from server.local_server import start_server, stop_server

class TestRequestsAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = start_server()
        cls.base_url = "http://localhost:8000"
        # Give the server a moment to start
        time.sleep(1)
    
    @classmethod
    def tearDownClass(cls):
        stop_server(cls.server)
    
    def test_get_request(self):
        response = requests.get(f"{self.base_url}/get", params={"key": "value"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["method"], "GET")
        self.assertEqual(data["args"]["key"], ["value"])
    
    def test_post_request(self):
        payload = {"key": "value"}
        response = requests.post(f"{self.base_url}/post", data=json.dumps(payload))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["method"], "POST")
        self.assertIn(json.dumps(payload), data["data"])
    
    def test_put_request(self):
        payload = {"key": "value"}
        response = requests.put(f"{self.base_url}/put", data=json.dumps(payload))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["method"], "PUT")
        self.assertIn(json.dumps(payload), data["data"])
    
    def test_delete_request(self):
        response = requests.delete(f"{self.base_url}/delete")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["method"], "DELETE")
    
    def test_patch_request(self):
        payload = {"key": "value"}
        response = requests.patch(f"{self.base_url}/patch", data=json.dumps(payload))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["method"], "PATCH")
        self.assertIn(json.dumps(payload), data["data"])
    
    def test_request_with_headers(self):
        headers = {"Custom-Header": "TestValue"}
        response = requests.get(f"{self.base_url}/headers", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Custom-Header", data)
        self.assertEqual(data["Custom-Header"], "TestValue")
    
    def test_status_codes(self):
        response = requests.get(f"{self.base_url}/status", params={"code": 404})
        self.assertEqual(response.status_code, 404)
        
        response = requests.get(f"{self.base_url}/status", params={"code": 201})
        self.assertEqual(response.status_code, 201)