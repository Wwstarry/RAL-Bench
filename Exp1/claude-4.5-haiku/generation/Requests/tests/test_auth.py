import pytest
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth


class TestAuth:
    """Test authentication helpers."""
    
    def test_basic_auth_success(self, base_url):
        """Test successful basic authentication."""
        auth = HTTPBasicAuth("user", "pass")
        response = requests.get(f"{base_url}/auth", auth=auth)
        assert response.status_code == 200
        assert response.json()["authenticated"] is True
    
    def test_basic_auth_with_tuple(self, base_url):
        """Test basic authentication with tuple."""
        response = requests.get(f"{base_url}/auth", auth=("user", "pass"))
        assert response.status_code == 200
        assert response.json()["authenticated"] is True
    
    def test_basic_auth_failure(self, base_url):
        """Test failed basic authentication."""
        response = requests.get(f"{base_url}/auth")
        assert response.status_code == 401
        assert response.json()["authenticated"] is False
    
    def test_basic_auth_header_format(self, base_url):
        """Test basic auth header format."""
        auth = HTTPBasicAuth("user", "pass")
        response = requests.get(f"{base_url}/auth", auth=auth)
        assert "Authorization" in response.request.headers
        assert response.request.headers["Authorization"].startswith("Basic ")
    
    def test_auth_with_session(self, base_url):
        """Test authentication with session."""
        session = requests.Session()
        session.auth = HTTPBasicAuth("user", "pass")
        response = session.get(f"{base_url}/auth")
        assert response.status_code == 200
        session.close()