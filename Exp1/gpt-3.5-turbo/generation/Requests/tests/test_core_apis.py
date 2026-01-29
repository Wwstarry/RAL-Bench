import http.server
import socketserver
import threading
import base64
import json
import pytest
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout

PORT = 8000

class TestHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Hello, world!")
        elif self.path == "/json":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"message": "Hello, JSON"}
            self.wfile.write(json.dumps(response).encode())
        elif self.path == "/auth":
            auth_header = self.headers.get("Authorization")
            if auth_header is None:
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="Test"')
                self.end_headers()
            else:
                auth_type, encoded = auth_header.split(" ", 1)
                if auth_type.lower() == "basic":
                    decoded = base64.b64decode(encoded).decode()
                    username, password = decoded.split(":", 1)
                    if username == "user" and password == "pass":
                        self.send_response(200)
                        self.send_header("Content-type", "text/plain")
                        self.end_headers()
                        self.wfile.write(b"Authenticated")
                        return
                self.send_response(403)
                self.end_headers()
        elif self.path == "/cookies":
            cookie = self.headers.get("Cookie")
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            if cookie:
                self.wfile.write(cookie.encode())
            else:
                self.wfile.write(b"No cookies")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/echo":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress logging to keep test output clean
        pass

@pytest.fixture(scope="module")
def http_server():
    handler = TestHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever)
        thread.daemon = True
        thread.start()
        yield
        httpd.shutdown()
        thread.join()

def test_requests_get(http_server):
    r = requests.get(f"http://localhost:{PORT}/")
    assert r.status_code == 200
    assert r.text == "Hello, world!"

def test_requests_get_json(http_server):
    r = requests.get(f"http://localhost:{PORT}/json")
    assert r.status_code == 200
    data = r.json()
    assert data["message"] == "Hello, JSON"

def test_requests_post_echo(http_server):
    data = b"Test POST data"
    r = requests.post(f"http://localhost:{PORT}/echo", data=data)
    assert r.status_code == 200
    assert r.content == data

def test_requests_auth_success(http_server):
    r = requests.get(f"http://localhost:{PORT}/auth", auth=HTTPBasicAuth("user", "pass"))
    assert r.status_code == 200
    assert r.text == "Authenticated"

def test_requests_auth_failure(http_server):
    r = requests.get(f"http://localhost:{PORT}/auth", auth=HTTPBasicAuth("user", "wrong"))
    assert r.status_code == 403

def test_requests_session_cookies(http_server):
    session = requests.Session()
    # Initially no cookies
    r = session.get(f"http://localhost:{PORT}/cookies")
    assert r.text == "No cookies"
    # Set cookie in session
    session.cookies.set("mycookie", "cookievalue")
    r = session.get(f"http://localhost:{PORT}/cookies")
    assert "mycookie=cookievalue" in r.text

def test_requests_prepared_request(http_server):
    s = requests.Session()
    req = requests.Request('GET', f"http://localhost:{PORT}/")
    prepped = s.prepare_request(req)
    r = s.send(prepped)
    assert r.status_code == 200
    assert r.text == "Hello, world!"

def test_requests_exceptions(http_server):
    # ConnectionError: connect to invalid port
    with pytest.raises(ConnectionError):
        requests.get("http://localhost:9999/", timeout=0.5)

    # Timeout
    with pytest.raises(Timeout):
        requests.get(f"http://localhost:{PORT}/", timeout=0.0001)

    # HTTPError on raise_for_status
    r = requests.get(f"http://localhost:{PORT}/notfound")
    assert r.status_code == 404
    with pytest.raises(HTTPError):
        r.raise_for_status()

def test_requests_session_adapter(http_server):
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter()
    session.mount("http://", adapter)
    r = session.get(f"http://localhost:{PORT}/")
    assert r.status_code == 200
    assert r.text == "Hello, world!"