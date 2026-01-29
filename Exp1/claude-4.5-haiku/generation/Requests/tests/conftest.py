import pytest
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time


class TestHTTPHandler(BaseHTTPRequestHandler):
    """Simple HTTP request handler for testing."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/get":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "method": "GET",
                "path": self.path,
                "headers": dict(self.headers),
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/get")
            self.end_headers()
        elif self.path == "/status/200":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": 200}).encode())
        elif self.path == "/status/404":
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": 404}).encode())
        elif self.path == "/status/500":
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": 500}).encode())
        elif self.path == "/cookies":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", "test_cookie=test_value")
            self.end_headers()
            self.wfile.write(json.dumps({"cookies": "set"}).encode())
        elif self.path == "/auth":
            auth_header = self.headers.get("Authorization", "")
            if auth_header.startswith("Basic "):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"authenticated": True}).encode())
            else:
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="test"')
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"authenticated": False}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        if self.path == "/post":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "method": "POST",
                "path": self.path,
                "headers": dict(self.headers),
                "body": body.decode() if body else "",
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_PUT(self):
        """Handle PUT requests."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        if self.path == "/put":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "method": "PUT",
                "path": self.path,
                "body": body.decode() if body else "",
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_DELETE(self):
        """Handle DELETE requests."""
        if self.path == "/delete":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"method": "DELETE", "path": self.path}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


@pytest.fixture(scope="session")
def http_server():
    """Start a local HTTP server for testing."""
    server = HTTPServer(("127.0.0.1", 0), TestHTTPHandler)
    host, port = server.server_address
    
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    time.sleep(0.1)
    
    yield f"http://{host}:{port}"
    
    server.shutdown()


@pytest.fixture
def base_url(http_server):
    """Provide base URL for tests."""
    return http_server