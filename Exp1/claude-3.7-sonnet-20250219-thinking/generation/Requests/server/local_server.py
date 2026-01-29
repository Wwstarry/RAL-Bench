import http.server
import socketserver
import json
import base64
import threading
import time
from urllib.parse import urlparse, parse_qs

PORT = 8000

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type='text/plain'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()
    
    def _check_auth(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Basic '):
            return False
        
        encoded = auth_header[6:] # Remove 'Basic '
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':')
        
        return username == 'testuser' and password == 'password'

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        
        if path == '/':
            self._set_headers(200)
            self.wfile.write(b"Local test server is running")
        
        elif path == '/get':
            self._set_headers(200, 'application/json')
            response = {
                'method': 'GET',
                'headers': dict(self.headers),
                'args': query,
            }
            self.wfile.write(json.dumps(response).encode())
        
        elif path == '/status':
            status_code = int(query.get('code', ['200'])[0])
            self._set_headers(status_code)
            self.wfile.write(f"Status code: {status_code}".encode())
        
        elif path == '/headers':
            self._set_headers(200, 'application/json')
            self.wfile.write(json.dumps(dict(self.headers)).encode())
        
        elif path == '/cookies':
            self._set_headers(200)
            self.send_header('Set-Cookie', 'test=value; Path=/')
            self.end_headers()
            self.wfile.write(b"Cookie set")
        
        elif path == '/redirect':
            redirect_to = query.get('url', ['/'])[0]
            self.send_response(302)
            self.send_header('Location', redirect_to)
            self.end_headers()
        
        elif path == '/auth/basic':
            if self._check_auth():
                self._set_headers(200)
                self.wfile.write(b"Authentication successful")
            else:
                self._set_headers(401)
                self.send_header('WWW-Authenticate', 'Basic realm="Test"')
                self.end_headers()
                self.wfile.write(b"Authentication required")
        
        elif path == '/timeout':
            delay = int(query.get('seconds', ['10'])[0])
            time.sleep(delay)
            self._set_headers(200)
            self.wfile.write(b"Response after delay")
        
        else:
            self._set_headers(404)
            self.wfile.write(b"Not found")

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        self._set_headers(200, 'application/json')
        response = {
            'method': 'POST',
            'headers': dict(self.headers),
            'data': post_data
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_PUT(self):
        content_length = int(self.headers.get('Content-Length', 0))
        put_data = self.rfile.read(content_length).decode('utf-8')
        
        self._set_headers(200, 'application/json')
        response = {
            'method': 'PUT',
            'headers': dict(self.headers),
            'data': put_data
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_DELETE(self):
        self._set_headers(200, 'application/json')
        response = {
            'method': 'DELETE',
            'headers': dict(self.headers)
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_PATCH(self):
        content_length = int(self.headers.get('Content-Length', 0))
        patch_data = self.rfile.read(content_length).decode('utf-8')
        
        self._set_headers(200, 'application/json')
        response = {
            'method': 'PATCH',
            'headers': dict(self.headers),
            'data': patch_data
        }
        self.wfile.write(json.dumps(response).encode())


def start_server():
    handler = RequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    print(f"Serving at port {PORT}")
    
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    return httpd

def stop_server(httpd):
    httpd.shutdown()
    httpd.server_close()