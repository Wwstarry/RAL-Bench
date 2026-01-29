import pytest
import requests
from requests.models import Request, Response, PreparedRequest


class TestModels:
    """Test Request/Response objects and preparation."""
    
    def test_response_status_code(self, base_url):
        """Test response status code."""
        response = requests.get(f"{base_url}/status/200")
        assert response.status_code == 200
    
    def test_response_headers(self, base_url):
        """Test response headers."""
        response = requests.get(f"{base_url}/get")
        assert "content-type" in response.headers
    
    def test_response_content(self, base_url):
        """Test response content."""
        response = requests.get(f"{base_url}/get")
        assert response.content is not None
        assert len(response.content) > 0
    
    def test_response_text(self, base_url):
        """Test response text."""
        response = requests.get(f"{base_url}/get")
        assert isinstance(response.text, str)
        assert len(response.text) > 0
    
    def test_response_json(self, base_url):
        """Test response JSON parsing."""
        response = requests.get(f"{base_url}/get")
        data = response.json()
        assert isinstance(data, dict)
        assert "method" in data
    
    def test_response_url(self, base_url):
        """Test response URL."""
        response = requests.get(f"{base_url}/get")
        assert response.url == f"{base_url}/get"
    
    def test_response_history(self, base_url):
        """Test response history for redirects."""
        response = requests.get(f"{base_url}/redirect", allow_redirects=True)
        assert len(response.history) > 0
        assert response.history[0].status_code == 302
    
    def test_response_cookies(self, base_url):
        """Test response cookies."""
        response = requests.get(f"{base_url}/cookies")
        assert "test_cookie" in response.cookies
    
    def test_response_elapsed(self, base_url):
        """Test response elapsed time."""
        response = requests.get(f"{base_url}/get")
        assert response.elapsed is not None
        assert response.elapsed.total_seconds() >= 0
    
    def test_request_preparation(self, base_url):
        """Test request preparation."""
        req = Request("GET", f"{base_url}/get")
        prepared = req.prepare()
        assert isinstance(prepared, PreparedRequest)
        assert prepared.method == "GET"
        assert prepared.url == f"{base_url}/get"
    
    def test_prepared_request_with_data(self, base_url):
        """Test prepared request with data."""
        req = Request("POST", f"{base_url}/post", json={"key": "value"})
        prepared = req.prepare()
        assert prepared.method == "POST"
        assert prepared.body is not None
    
    def test_prepared_request_with_headers(self, base_url):
        """Test prepared request with headers."""
        headers = {"X-Custom": "value"}
        req = Request("GET", f"{base_url}/get", headers=headers)
        prepared = req.prepare()
        assert "X-Custom" in prepared.headers
    
    def test_response_ok_property(self, base_url):
        """Test response ok property."""
        response = requests.get(f"{base_url}/status/200")
        assert response.ok is True
        
        response = requests.get(f"{base_url}/status/404")
        assert response.ok is False
    
    def test_response_is_redirect(self, base_url):
        """Test response is_redirect property."""
        response = requests.get(f"{base_url}/redirect", allow_redirects=False)
        assert response.is_redirect is True