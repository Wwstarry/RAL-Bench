import pytest
import threading
import time
import json
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

class Handler(BaseHTTPRequestHandler):
    """A custom handler for the local test server."""

    def _send_response(self, status_code, headers, body):
        self.send_response(status_code)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        if body is not None:
            self.wfile.write(body)

    def _send_json_response(self, data, status_code=200, headers=None):
        if headers is None:
            headers = {}
        body = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
        headers['Content-Length'] = str(len(body))
        self._send_response(status_code, headers, body)

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path
        query = parse_qs(url.query)

        if path == '/':
            self._send_json_response({"message": "hello world"})
        elif path == '/params':
            self._send_json_response({"params": query})
        elif path == '/headers':
            self._send_json_response({"headers": dict(self.headers)})
        elif path == '/cookies/set':
            headers = {'Set-Cookie': 'test_cookie=test_value; Path=/'}
            self._send_json_response({"status": "cookie set"}, headers=headers)
        elif path == '/cookies/get':
            cookie = self.headers.get('Cookie')
            if cookie and 'test_cookie=test_value' in cookie:
                self._send_json_response({"status": "cookie received"})
            else:
                self._send_json_response({"status": "cookie not found"}, status_code=400)
        elif path == '/auth':
            auth_header = self.headers.get('Authorization')
            if not auth_header:
                headers = {'WWW-Authenticate': 'Basic realm="Test"'}
                self._send_json_response({"error": "Authorization required"}, status_code=401, headers=headers)
                return
            
            try:
                auth_type, encoded_creds = auth_header.split(' ')
                if auth_type.lower() == 'basic':
                    creds = base64.b64decode(encoded_creds).decode('utf-8')
                    if creds == 'user:pass':
                        self._send_json_response({"status": "auth successful"})
                    else:
                        self._send_json_response({"error": "Invalid credentials"}, status_code=401)
                else:
                    self._send_json_response({"error": "Unsupported auth type"}, status_code=400)
            except Exception:
                self._send_json_response({"error": "Invalid Authorization header"}, status_code=400)
        elif path == '/timeout':
            time.sleep(0.5)
            self._send_json_response({"status": "finally responded"})
        elif path.startswith('/redirect/'):
            try:
                count = int(path.split('/')[-1])
                if count > 0:
                    location = f'/redirect/{count - 1}'
                    headers = {'Location': location}
                    self._send_response(302, headers, None)
                else:
                    self._send_json_response({"status": "redirect finished"})
            except ValueError:
                self._send_json_response({"error": "Invalid redirect count"}, status_code=400)
        elif path.startswith('/status/'):
            try:
                code = int(path.split('/')[-1])
                self._send_json_response({"status_code": code}, status_code=code)
            except ValueError:
                self._send_json_response({"error": "Invalid status code"}, status_code=400)
        else:
            self._send_json_response({"error": "Not Found"}, status_code=404)

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == '/echo':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            content_type = self.headers.get('Content-Type', '')
            
            response_data = {
                "headers": dict(self.headers),
                "body": post_data.decode('utf-8')
            }
            if 'application/json' in content_type:
                try:
                    response_data['json'] = json.loads(post_data)
                except json.JSONDecodeError:
                    response_data['json_error'] = "Invalid JSON"

            self._send_json_response(response_data)
        else:
            self._send_json_response({"error": "Not Found"}, status_code=404)

    def do_PUT(self):
        # For echo, PUT is the same as POST
        self.do_POST()

    def do_DELETE(self):
        if urlparse(self.path).path == '/delete':
            self._send_json_response({"status": "deleted"})
        else:
            self._send_json_response({"error": "Not Found"}, status_code=404)

    def do_HEAD(self):
        if urlparse(self.path).path == '/':
            headers = {'Content-Type': 'application/json', 'Content-Length': '27'}
            self._send_response(200, headers, None)
        else:
            self._send_response(404, {}, None)

    def do_OPTIONS(self):
        if urlparse(self.path).path == '/':
            headers = {'Allow': 'GET, HEAD, POST, OPTIONS'}
            self._send_json_response({"allowed": ["GET", "HEAD", "POST", "OPTIONS"]}, headers=headers)
        else:
            self._send_json_response({"error": "Not Found"}, status_code=404)

    def log_message(self, format, *args):
        # Suppress logging to keep test output clean
        return

@pytest.fixture(scope="session")
def local_server():
    """Starts a local HTTP server in a background thread for testing."""
    # Use port 0 to let the OS pick a free port
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    port = server.server_port
    
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    yield f"http://127.0.0.1:{port}"
    
    server.shutdown()
    server.server_close()
    server_thread.join()