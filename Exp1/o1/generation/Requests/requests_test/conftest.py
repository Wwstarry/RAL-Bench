import pytest
import socket
import threading
import base64
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

class TestRequestHandler(BaseHTTPRequestHandler):
    def _extract_auth_credentials(self):
        """
        Returns (username, password) if Basic auth header exists, else (None, None).
        """
        auth_header = self.headers.get('Authorization')
        if auth_header and auth_header.startswith('Basic '):
            encoded = auth_header.split(' ', 1)[1].strip()
            decoded = base64.b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)
            return username, password
        return None, None

    def _send_text_response(self, code, text, content_type='text/plain'):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.end_headers()
        if text:
            self.wfile.write(text.encode('utf-8'))

    def _handle_basic_routes(self, parsed_path):
        """
        Handles some example GET endpoints:
         - '/' -> returns "Hello, world!"
         - '/echo?msg=...' -> echoes the query msg
         - '/authenticated' -> requires Basic auth
         - '/status/<code>' -> returns that HTTP code
        """
        if parsed_path.path == '/':
            self._send_text_response(200, 'Hello, world!')
        elif parsed_path.path == '/echo':
            qs = urllib.parse.parse_qs(parsed_path.query)
            msg = qs.get('msg', [''])[0]
            self._send_text_response(200, 'Echo: ' + msg)
        elif parsed_path.path.startswith('/status/'):
            try:
                code_str = parsed_path.path.split('/')[-1]
                code = int(code_str)
            except ValueError:
                code = 200
            self._send_text_response(code, f"Returned status {code}")
        elif parsed_path.path == '/authenticated':
            user, pw = self._extract_auth_credentials()
            if user == 'admin' and pw == 'secret':
                self._send_text_response(200, 'Authenticated')
            else:
                self._send_text_response(401, 'Unauthorized')
        else:
            self._send_text_response(404, 'Not Found')

    def do_GET(self):
        parsed_path = urllib.parse.urlsplit(self.path)
        self._handle_basic_routes(parsed_path)

    def do_POST(self):
        """
        If path is '/post', respond with the received request data.
        Else 404.
        """
        parsed_path = urllib.parse.urlsplit(self.path)
        if parsed_path.path == '/post':
            length = int(self.headers.get('Content-Length', 0))
            raw_data = self.rfile.read(length).decode('utf-8')
            self._send_text_response(200, "Received: " + raw_data)
        else:
            self._send_text_response(404, 'Not Found')

@pytest.fixture(scope="session")
def server():
    """
    Spins up a local HTTP server on an ephemeral port, yields the base URL,
    and shuts down when tests finish.
    """
    def _run_server(httpd):
        with httpd:
            httpd.serve_forever()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0))
    host, port = sock.getsockname()
    sock.close()

    server_address = (host, port)
    httpd = HTTPServer(server_address, TestRequestHandler)

    thread = threading.Thread(target=_run_server, args=(httpd,), daemon=True)
    thread.start()
    base_url = f'http://{host}:{port}'
    yield base_url
    httpd.shutdown()
    thread.join()