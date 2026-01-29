import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError, Timeout

# Local HTTP server for testing
class TestHTTPServerRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/success":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Success")
        elif self.path == "/timeout":
            pass  # Simulate a timeout by not responding
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/echo":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(post_data)
        else:
            self.send_response(404)
            self.end_headers()

def run_test_server():
    server = HTTPServer(("localhost", 8080), TestHTTPServerRequestHandler)
    server.serve_forever()

class TestRequestsAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server_thread = threading.Thread(target=run_test_server, daemon=True)
        cls.server_thread.start()

    def test_get_success(self):
        response = requests.get("http://localhost:8080/success")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Success")

    def test_get_not_found(self):
        response = requests.get("http://localhost:8080/notfound")
        self.assertEqual(response.status_code, 404)

    def test_post_echo(self):
        data = {"key": "value"}
        response = requests.post("http://localhost:8080/echo", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), data)

    def test_timeout(self):
        with self.assertRaises(Timeout):
            requests.get("http://localhost:8080/timeout", timeout=1)

class TestRequestsSession(unittest.TestCase):
    def test_session_cookies(self):
        session = requests.Session()
        session.cookies.set("test_cookie", "test_value")
        self.assertEqual(session.cookies.get("test_cookie"), "test_value")

    def test_session_persistent_headers(self):
        session = requests.Session()
        session.headers.update({"User-Agent": "test-agent"})
        response = session.get("http://localhost:8080/success")
        self.assertEqual(response.request.headers["User-Agent"], "test-agent")

class TestRequestsAuth(unittest.TestCase):
    def test_basic_auth(self):
        with self.assertRaises(HTTPError):
            response = requests.get(
                "http://localhost:8080/protected",
                auth=HTTPBasicAuth("user", "wrongpassword"),
            )
            response.raise_for_status()

if __name__ == "__main__":
    unittest.main()