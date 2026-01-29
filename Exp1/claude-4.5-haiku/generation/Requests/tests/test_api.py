import pytest
import requests
from requests.exceptions import RequestException, ConnectionError


class TestRequestsAPI:
    """Test high-level request helpers from requests.api."""
    
    def test_get_request(self, base_url):
        """Test GET request."""
        response = requests.get(f"{base_url}/get")
        assert response.status_code == 200
        assert response.json()["method"] == "GET"
    
    def test_post_request(self, base_url):
        """Test POST request."""
        data = {"key": "value"}
        response = requests.post(f"{base_url}/post", json=data)
        assert response.status_code == 200
        assert response.json()["method"] == "POST"
    
    def test_put_request(self, base_url):
        """Test PUT request."""
        data = {"key": "updated"}
        response = requests.put(f"{base_url}/put", json=data)
        assert response.status_code == 200
        assert response.json()["method"] == "PUT"
    
    def test_delete_request(self, base_url):
        """Test DELETE request."""
        response = requests.delete(f"{base_url}/delete")
        assert response.status_code == 200
        assert response.json()["method"] == "DELETE"
    
    def test_head_request(self, base_url):
        """Test HEAD request."""
        response = requests.head(f"{base_url}/get")
        assert response.status_code == 200
    
    def test_options_request(self, base_url):
        """Test OPTIONS request."""
        response = requests.options(f"{base_url}/get")
        assert response.status_code in [200, 404]
    
    def test_request_with_params(self, base_url):
        """Test request with query parameters."""
        params = {"key": "value", "foo": "bar"}
        response = requests.get(f"{base_url}/get", params=params)
        assert response.status_code == 200
        assert "key=value" in response.url or "foo=bar" in response.url
    
    def test_request_with_headers(self, base_url):
        """Test request with custom headers."""
        headers = {"X-Custom-Header": "test-value"}
        response = requests.get(f"{base_url}/get", headers=headers)
        assert response.status_code == 200
    
    def test_request_with_timeout(self, base_url):
        """Test request with timeout."""
        response = requests.get(f"{base_url}/get", timeout=5)
        assert response.status_code == 200
    
    def test_request_allow_redirects(self, base_url):
        """Test request with redirect following."""
        response = requests.get(f"{base_url}/redirect", allow_redirects=True)
        assert response.status_code == 200
        assert response.json()["method"] == "GET"
    
    def test_request_no_redirects(self, base_url):
        """Test request without following redirects."""
        response = requests.get(f"{base_url}/redirect", allow_redirects=False)
        assert response.status_code == 302