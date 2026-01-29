"""
Test requests.sessions module - Session lifecycle, cookies, adapters.
"""
import json
import requests
from server import TestServer

class TestSessions:
    """Test requests.sessions module."""
    
    @classmethod
    def setup_class(cls):
        """Start test server."""
        cls.server = TestServer()
        cls.server.start()
        cls.base_url = cls.server.base_url
    
    @classmethod
    def teardown_class(cls):
        """Stop test server."""
        cls.server.stop()
    
    def test_session_persistence(self):
        """Test session persistence across requests."""
        session = requests.Session()
        
        # First request
        response1 = session.get(f'{self.base_url}/cookies')
        assert response1.status_code == 200
        
        # Second request should have cookie from first request
        response2 = session.get(f'{self.base_url}/headers')
        assert response2.status_code == 200
        headers = response2.json()
        assert 'test_cookie=test_value' in headers.get('Cookie', '')
        
        session.close()
    
    def test_session_headers(self):
        """Test session-level headers."""
        session = requests.Session()
        session.headers.update({
            'X-Session-Header': 'SessionValue',
            'User-Agent': 'SessionAgent/1.0'
        })
        
        response = session.get(f'{self.base_url}/headers')
        assert response.status_code == 200
        headers = response.json()
        assert headers['X-Session-Header'] == 'SessionValue'
        assert headers['User-Agent'] == 'SessionAgent/1.0'
        
        # Override session header with request header
        response = session.get(f'{self.base_url}/headers', headers={'User-Agent': 'RequestAgent/1.0'})
        headers = response.json()
        assert headers['User-Agent'] == 'RequestAgent/1.0'
        assert headers['X-Session-Header'] == 'SessionValue'
        
        session.close()
    
    def test_session_cookies(self):
        """Test session cookie management."""
        session = requests.Session()
        
        # Set cookie manually
        session.cookies.set('manual_cookie', 'manual_value')
        
        # Make request to get server cookie
        response = session.get(f'{self.base_url}/cookies')
        assert response.status_code == 200
        
        # Check both cookies are present
        cookies = session.cookies.get_dict()
        assert 'manual_cookie' in cookies
        assert cookies['manual_cookie'] == 'manual_value'
        assert 'test_cookie' in cookies
        assert cookies['test_cookie'] == 'test_value'
        
        session.close()
    
    def test_session_auth(self):
        """Test session-level authentication."""
        from requests.auth import HTTPBasicAuth
        
        session = requests.Session()
        session.auth = HTTPBasicAuth('testuser', 'testpass')
        
        response = session.get(f'{self.base_url}/auth/basic')
        assert response.status_code == 200
        data = response.json()
        assert data['authenticated'] is True
        assert data['user'] == 'testuser'
        
        session.close()
    
    def test_session_adapters(self):
        """Test session adapters."""
        session = requests.Session()
        
        # Get default adapter
        adapter = session.get_adapter(f'{self.base_url}/')
        assert adapter is not None
        
        # Create and mount custom adapter
        from requests.adapters import HTTPAdapter
        custom_adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10)
        
        # Mount for specific prefix
        session.mount('http://', custom_adapter)
        session.mount('https://', custom_adapter)
        
        # Make request using custom adapter
        response = session.get(f'{self.base_url}/')
        assert response.status_code == 200
        
        session.close()
    
    def test_session_context_manager(self):
        """Test session as context manager."""
        with requests.Session() as session:
            session.headers['X-Test'] = 'Value'
            response = session.get(f'{self.base_url}/headers')
            assert response.status_code == 200
            headers = response.json()
            assert headers['X-Test'] == 'Value'
        
        # Session should be closed
        assert session.closed is True
    
    def test_session_prepare_request(self):
        """Test request preparation."""
        session = requests.Session()
        
        # Create a request
        request = requests.Request(
            'GET',
            f'{self.base_url}/headers',
            headers={'X-Custom': 'Value'}
        )
        
        # Prepare the request
        prepared = session.prepare_request(request)
        
        # Send the prepared request
        response = session.send(prepared)
        assert response.status_code == 200
        headers = response.json()
        assert headers['X-Custom'] == 'Value'
        
        session.close()
    
    def test_session_merge_parameters(self):
        """Test parameter merging between session and request."""
        session = requests.Session()
        session.params = {'session_param': 'session_value'}
        
        # Request with its own params
        response = session.get(
            f'{self.base_url}/query',
            params={'request_param': 'request_value'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['session_param'][0] == 'session_value'
        assert data['request_param'][0] == 'request_value'
        
        session.close()
    
    def test_session_redirects(self):
        """Test session redirect handling."""
        session = requests.Session()
        
        # Follow redirects (default)
        response = session.get(f'{self.base_url}/redirect')
        assert response.status_code == 200
        assert response.text == 'Redirect complete'
        assert len(response.history) == 3  # 3 redirects
        
        # Don't follow redirects
        response = session.get(f'{self.base_url}/redirect', allow_redirects=False)
        assert response.status_code == 302
        assert len(response.history) == 0
        
        session.close()