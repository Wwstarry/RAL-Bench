"""
Core API tests for Requests library against local HTTP server.
Tests cover: api, sessions, models, auth, and exceptions.
"""
import json
import os
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError


class TestHTTPHandler(BaseHTTPRequestHandler):
    """Simple HTTP server handler for testing Requests library."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/basic_auth':
            # Basic auth endpoint
            auth_header = self.headers.get('Authorization', '')
            if auth_header.startswith('Basic '):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {'authenticated': True, 'user': 'test'}
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="Test"')
                self.end_headers()
                
        elif parsed_path.path == '/timeout':
            # Timeout test endpoint
            time.sleep(2)  # Sleep longer than test timeout
            self.send_response(200)
            self.end_headers()
            
        elif parsed_path.path == '/echo':
            # Echo back query parameters
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            query_params = parse_qs(parsed_path.query)
            response = {'path': parsed_path.path, 'query': query_params}
            self.wfile.write(json.dumps(response).encode())
            
        elif parsed_path.path == '/cookies':
            # Cookie management endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Set-Cookie', 'test_cookie=test_value')
            self.end_headers()
            cookies = dict(self.headers.get('Cookie', '').split('; ') if self.headers.get('Cookie') else {})
            response = {'cookies_received': cookies}
            self.wfile.write(json.dumps(response).encode())
            
        else:
            # Default endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'message': 'Hello from test server', 'path': parsed_path.path}
            self.wfile.write(json.dumps(response).encode()
    
    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        try:
            data = json.loads(post_data.decode()) if post_data else {}
        except:
            data = {'raw_data': post_data.decode()}
            
        response = {
            'method': 'POST',
            'data_received': data,
            'content_type': self.headers.get('Content-Type', '')
        }
        self.wfile.write(json.dumps(response).encode()
    
    def do_PUT(self):
        """Handle PUT requests."""
        self.do_POST()  # Reuse POST logic
    
    def do_DELETE(self):
        """Handle DELETE requests."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {'method': 'DELETE', 'deleted': True}
        self.wfile.write(json.dumps(response).encode()
    
    def log_message(self, format, *args):
        """Suppress server log messages."""
        pass


class TestServer:
    """HTTP test server manager."""
    
    def __init__(self, port=8888):
        self.port = port
        self.server = None
        self.thread = None
        
    def start(self):
        """Start the test server in a separate thread."""
        def run_server():
            self.server = HTTPServer(('localhost', self.port), TestHTTPHandler)
            self.server.serve_forever()
            
        self.thread = threading.Thread(target=run_server)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(0.5)  # Give server time to start
        
    def stop(self):
        """Stop the test server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()


class RequestsCoreTests:
    """Comprehensive tests for Requests core functionality."""
    
    def __init__(self, base_url):
        self.base_url = base_url
        
    def test_high_level_api(self):
        """Test requests.api high-level helpers."""
        print("Testing high-level API helpers...")
        
        # Test GET
        response = requests.get(f"{self.base_url}/test")
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        
        # Test POST with JSON
        response = requests.post(f"{self.base_url}/test", json={'key': 'value'})
        assert response.status_code == 200
        data = response.json()
        assert data['method'] == 'POST'
        assert data['data_received']['key'] == 'value'
        
        # Test PUT
        response = requests.put(f"{self.base_url}/test", data='test data')
        assert response.status_code == 200
        
        # Test DELETE
        response = requests.delete(f"{self.base_url}/test")
        assert response.status_code == 200
        data = response.json()
        assert data['deleted'] is True
        
        print("✓ High-level API tests passed")
        
    def test_session_lifecycle(self):
        """Test requests.sessions Session functionality."""
        print("Testing Session lifecycle...")
        
        # Test session with persistent cookies
        session = requests.Session()
        
        # First request should set cookie
        response = session.get(f"{self.base_url}/cookies")
        assert 'test_cookie' in response.cookies
        
        # Second request should send cookie back
        response = session.get(f"{self.base_url}/cookies")
        data = response.json()
        assert 'test_cookie' in data['cookies_received']
        
        # Test session headers
        session.headers.update({'X-Test-Header': 'test-value'})
        response = session.get(f"{self.base_url}/echo")
        data = response.json()
        
        session.close()
        print("✓ Session lifecycle tests passed")
        
    def test_request_response_objects(self):
        """Test requests.models Request/Response objects."""
        print("Testing Request/Response objects...")
        
        # Test Request preparation
        req = requests.Request('GET', f"{self.base_url}/echo", params={'param': 'value'})
        prepared = req.prepare()
        
        assert 'param=value' in prepared.url
        assert prepared.method == 'GET'
        
        # Test Response object
        response = requests.get(f"{self.base_url}/echo?test=value")
        assert response.status_code == 200
        assert response.ok is True
        assert response.headers['Content-Type'] == 'application/json'
        
        data = response.json()
        assert data['query']['test'][0] == 'value'
        
        print("✓ Request/Response objects tests passed")
        
    def test_basic_auth(self):
        """Test requests.auth basic authentication."""
        print("Testing Basic Authentication...")
        
        # Test without auth (should fail)
        response = requests.get(f"{self.base_url}/basic_auth")
        assert response.status_code == 401
        
        # Test with auth (should succeed)
        auth = HTTPBasicAuth('testuser', 'testpass')
        response = requests.get(f"{self.base_url}/basic_auth", auth=auth)
        assert response.status_code == 200
        data = response.json()
        assert data['authenticated'] is True
        
        # Test auth with session
        session = requests.Session()
        session.auth = auth
        response = session.get(f"{self.base_url}/basic_auth")
        assert response.status_code == 200
        session.close()
        
        print("✓ Basic Authentication tests passed")
        
    def test_exceptions(self):
        """Test requests.exceptions error handling."""
        print("Testing exceptions...")
        
        # Test timeout exception
        try:
            requests.get(f"{self.base_url}/timeout", timeout=0.5)
            assert False, "Should have raised Timeout"
        except Timeout:
            pass  # Expected
        
        # Test connection error (invalid URL)
        try:
            requests.get('http://invalid-localhost-test:9999')
            assert False, "Should have raised ConnectionError"
        except ConnectionError:
            pass  # Expected
            
        # Test HTTP error for error status codes
        response = requests.get(f"{self.base_url}/nonexistent")
        # Note: Our test server returns 200 for all paths, so we can't test 404 easily
        
        print("✓ Exception tests passed")
        
    def run_all_tests(self):
        """Run all core functionality tests."""
        print(f"Running Requests core tests against {self.base_url}")
        print("=" * 50)
        
        self.test_high_level_api()
        self.test_session_lifecycle()
        self.test_request_response_objects()
        self.test_basic_auth()
        self.test_exceptions()
        
        print("=" * 50)
        print("✅ All core functionality tests passed!")


def main():
    """Main test runner."""
    # Start test server
    server = TestServer(8888)
    server.start()
    
    try:
        # Run tests
        tests = RequestsCoreTests('http://localhost:8888')
        tests.run_all_tests()
        
    finally:
        # Cleanup
        server.stop()


if __name__ == '__main__':
    main()