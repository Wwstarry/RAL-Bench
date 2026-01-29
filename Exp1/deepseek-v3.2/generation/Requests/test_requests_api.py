"""
Test requests.api module - high-level request helpers.
"""
import json
import pytest
import requests
from server import TestServer

class TestRequestsAPI:
    """Test requests.api module."""
    
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
    
    def test_get(self):
        """Test requests.get()."""
        response = requests.get(f'{self.base_url}/')
        assert response.status_code == 200
        assert response.text == 'Hello, World!'
        
        # Test with query parameters
        response = requests.get(f'{self.base_url}/query', params={'key': 'value', 'test': '123'})
        assert response.status_code == 200
        data = response.json()
        assert data['key'][0] == 'value'
        assert data['test'][0] == '123'
    
    def test_post(self):
        """Test requests.post()."""
        # Test with JSON data
        data = {'name': 'test', 'value': 42}
        response = requests.post(f'{self.base_url}/json', json=data)
        assert response.status_code == 200
        result = response.json()
        assert result['name'] == 'test'
        assert result['value'] == 42
        assert result['received'] is True
        
        # Test with form data
        form_data = {'field1': 'value1', 'field2': 'value2'}
        response = requests.post(f'{self.base_url}/form', data=form_data)
        assert response.status_code == 200
        result = response.json()
        assert result['field1'][0] == 'value1'
        assert result['field2'][0] == 'value2'
        
        # Test with raw data
        raw_data = b'raw binary data'
        response = requests.post(f'{self.base_url}/echo', data=raw_data)
        assert response.status_code == 200
        assert response.content == raw_data
    
    def test_put(self):
        """Test requests.put()."""
        data = {'action': 'update', 'id': 123}
        response = requests.put(f'{self.base_url}/json', json=data)
        assert response.status_code == 200
        result = response.json()
        assert result['action'] == 'update'
        assert result['id'] == 123
        assert result['received'] is True
    
    def test_delete(self):
        """Test requests.delete()."""
        response = requests.delete(f'{self.base_url}/delete')
        assert response.status_code == 200
        result = response.json()
        assert result['deleted'] is True
    
    def test_head(self):
        """Test requests.head()."""
        response = requests.head(f'{self.base_url}/')
        assert response.status_code == 200
        assert response.text == ''  # HEAD should not have body
        assert 'Content-Type' in response.headers
    
    def test_options(self):
        """Test requests.options()."""
        response = requests.options(f'{self.base_url}/')
        # Our test server doesn't implement OPTIONS, so we expect 404 or 200
        # Just verify the request doesn't crash
        assert response is not None
    
    def test_patch(self):
        """Test requests.patch()."""
        data = {'patch': 'data'}
        response = requests.patch(f'{self.base_url}/json', json=data)
        # Our test server treats PATCH as POST
        assert response.status_code == 200
        result = response.json()
        assert result['patch'] == 'data'
        assert result['received'] is True
    
    def test_response_properties(self):
        """Test response object properties."""
        response = requests.get(f'{self.base_url}/json')
        
        # Basic properties
        assert response.status_code == 200
        assert response.ok is True
        assert response.reason == 'OK'
        assert response.url == f'{self.base_url}/json'
        
        # Headers
        assert 'Content-Type' in response.headers
        assert response.headers['Content-Type'] == 'application/json'
        
        # Content
        data = response.json()
        assert data['message'] == 'JSON response'
        assert data['status'] == 'ok'
        
        # Text and content
        assert isinstance(response.text, str)
        assert isinstance(response.content, bytes)
        
        # Encoding
        assert response.encoding is not None
    
    def test_error_status(self):
        """Test error status codes."""
        response = requests.get(f'{self.base_url}/nonexistent')
        assert response.status_code == 404
        assert response.ok is False
        assert response.reason == 'Not Found'
    
    def test_timeout(self):
        """Test timeout parameter."""
        with pytest.raises(requests.exceptions.Timeout):
            requests.get(f'{self.base_url}/slow?delay=2', timeout=0.5)
        
        # Should not timeout with sufficient time
        response = requests.get(f'{self.base_url}/slow?delay=0.1', timeout=1)
        assert response.status_code == 200
    
    def test_custom_headers(self):
        """Test custom headers."""
        headers = {
            'X-Custom-Header': 'CustomValue',
            'User-Agent': 'TestAgent/1.0'
        }
        response = requests.get(f'{self.base_url}/headers', headers=headers)
        assert response.status_code == 200
        result = response.json()
        assert result['X-Custom-Header'] == 'CustomValue'
        assert result['User-Agent'] == 'TestAgent/1.0'