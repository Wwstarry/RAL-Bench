#!/usr/bin/env python3
"""
Simple HTTP server for testing requests library.
Supports various endpoints to test different features.
"""
import json
import base64
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class TestRequestHandler(BaseHTTPRequestHandler):
    """Handler for test endpoints."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Hello, World!')
            
        elif path == '/json':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            data = {'message': 'JSON response', 'status': 'ok'}
            self.wfile.write(json.dumps(data).encode())
            
        elif path == '/query':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(query).encode())
            
        elif path == '/headers':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            headers = dict(self.headers)
            self.wfile.write(json.dumps(headers).encode())
            
        elif path == '/cookies':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Set-Cookie', 'test_cookie=test_value')
            self.end_headers()
            cookies = self.headers.get('Cookie', '')
            self.wfile.write(json.dumps({'cookies': cookies}).encode())
            
        elif path == '/redirect':
            if 'count' in query:
                count = int(query['count'][0])
                if count < 3:
                    self.send_response(302)
                    self.send_header('Location', f'/redirect?count={count + 1}')
                    self.end_headers()
                else:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Redirect complete')
            else:
                self.send_response(302)
                self.send_header('Location', '/redirect?count=1')
                self.end_headers()
                
        elif path == '/slow':
            delay = float(query.get('delay', [1])[0])
            time.sleep(delay)
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Slow response')
            
        elif path == '/auth/basic':
            auth_header = self.headers.get('Authorization', '')
            if auth_header.startswith('Basic '):
                encoded = auth_header[6:]
                decoded = base64.b64decode(encoded).decode()
                username, password = decoded.split(':', 1)
                if username == 'testuser' and password == 'testpass':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'authenticated': True, 'user': username}).encode())
                    return
            
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Test Realm"')
            self.end_headers()
            self.wfile.write(b'Unauthorized')
            
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''
        
        if path == '/echo':
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.end_headers()
            self.wfile.write(body)
            
        elif path == '/json':
            try:
                data = json.loads(body.decode())
                data['received'] = True
                response = json.dumps(data)
            except:
                response = json.dumps({'error': 'Invalid JSON'})
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response.encode())
            
        elif path == '/form':
            form_data = parse_qs(body.decode())
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(form_data).encode())
            
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_PUT(self):
        """Handle PUT requests."""
        self.do_POST()
    
    def do_DELETE(self):
        """Handle DELETE requests."""
        if self.path == '/delete':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'deleted': True}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Suppress log messages."""
        pass

class TestServer:
    """Test HTTP server wrapper."""
    
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server = HTTPServer((host, port), TestRequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
    
    def start(self):
        """Start the server."""
        self.thread.start()
        time.sleep(0.5)  # Give server time to start
    
    def stop(self):
        """Stop the server."""
        self.server.shutdown()
        self.server.server_close()
    
    @property
    def base_url(self):
        """Get base URL for the server."""
        return f'http://{self.host}:{self.port}'

if __name__ == '__main__':
    server = TestServer()
    print(f'Starting test server at {server.base_url}')
    server.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nStopping server...')
        server.stop()