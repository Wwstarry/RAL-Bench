import http.server
import socketserver
import json
import time
import base64
import threading
from urllib.parse import urlparse, parse_qs

PORT = 8081
HOST = "localhost"
BASE_URL = f"http://{HOST}:{PORT}"

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/get':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            query = parse_qs(parsed.query)
            # Flatten query params for simplicity in this demo
            flat_query = {k: v[0] for k, v in query.items()}
            self.wfile.write(json.dumps({'args': flat_query, 'headers': dict(self.headers)}).encode('utf-8'))
            
        elif path == '/cookies':
            self.send_response(200)
            query = parse_qs(parsed.query)
            if 'set-name' in query and 'set-value' in query:
                self.send_header('Set-Cookie', f"{query['set-name'][0]}={query['set-value'][0]}; Path=/")
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            cookie_header = self.headers.get('Cookie', '')
            self.wfile.write(json.dumps({'cookies': cookie_header}).encode('utf-8'))

        elif path.startswith('/basic-auth/'):
            # Format: /basic-auth/{user}/{passwd}
            parts = path.strip('/').split('/')
            if len(parts) == 3:
                expected_user = parts[1]
                expected_pass = parts[2]
                auth_header = self.headers.get('Authorization')
                
                if not auth_header:
                    self._send_auth_challenge()
                    return
                
                try:
                    auth_type, encoded = auth_header.split(' ', 1)
                    if auth_type.lower() == 'basic':
                        decoded = base64.b64decode(encoded).decode('utf-8')
                        user, passwd = decoded.split(':', 1)
                        if user == expected_user and passwd == expected_pass:
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({'authenticated': True, 'user': user}).encode('utf-8'))
                            return
                except Exception:
                    pass
                
                self._send_auth_challenge()
            else:
                self.send_response(404)
                self.end_headers()

        elif path == '/status/500':
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Internal Server Error")

        elif path == '/timeout':
            # Sleep longer than the client timeout
            time.sleep(2)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Delayed response")

        else:
            self.send_response(404)
            self.end_headers()

    def _send_auth_challenge(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Test"')
        self.end_headers()

    def do_POST(self):
        self._handle_body_method()

    def do_PUT(self):
        self._handle_body_method()
        
    def do_DELETE(self):
        self._handle_body_method()

    def _handle_body_method(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        data = None
        try:
            if body:
                data = json.loads(body)
        except:
            data = body
            
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {
            'method': self.command,
            'data': data,
            'headers': dict(self.headers)
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

class ServerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.server = socketserver.TCPServer((HOST, PORT), RequestHandler)
        self.server.allow_reuse_address = True
        self.daemon = True

    def run(self):
        print(f"Starting local server on {BASE_URL}...")
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()