import pytest
import requests
from requests.sessions import Session
from requests.auth import HTTPBasicAuth


class TestIntegration:
    """Integration tests combining multiple features."""
    
    def test_session_with_auth_and_cookies(self, base_url):
        """Test session with authentication and cookies."""
        session = Session()
        session.auth = HTTPBasicAuth("user", "pass")
        
        response = session.get(f"{base_url}/cookies")
        assert response.status_code == 200
        assert "test_cookie" in session.cookies
        
        session.close()
    
    def test_multiple_requests_with_headers_and_auth(self, base_url):
        """Test multiple requests with headers and auth."""
        session = Session()
        session.headers.update({"X-Custom": "value"})
        session.auth = HTTPBasicAuth("user", "pass")
        
        response1 = session.get(f"{base_url}/get")
        assert response1.status_code == 200
        
        response2 = session.post(f"{base_url}/post", json={"data": "test"})
        assert response2.status_code == 200
        
        session.close()
    
    def test_request_response_cycle(self, base_url):
        """Test complete request-response cycle."""
        data = {"key": "value", "nested": {"inner": "data"}}
        response = requests.post(f"{base_url}/post", json=data)
        
        assert response.status_code == 200
        assert response.ok is True
        assert response.headers["content-type"] == "application/json"
        
        response_data = response.json()
        assert response_data["method"] == "POST"
    
    def test_session_with_custom_adapter(self, base_url):
        """Test session with custom adapter configuration."""
        session = Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        response = session.get(f"{base_url}/get")
        assert response.status_code == 200
        
        session.close()
    
    def test_prepared_request_execution(self, base_url):
        """Test prepared request execution."""
        from requests.models import Request
        
        req = Request(
            "POST",
            f"{base_url}/post",
            json={"key": "value"},
            headers={"X-Custom": "header"}
        )
        prepared = req.prepare()
        
        session = Session()
        response = session.send(prepared)
        assert response.status_code == 200
        session.close()
    
    def test_error_handling_with_session(self, base_url):
        """Test error handling with session."""
        session = Session()
        
        response = session.get(f"{base_url}/status/404")
        assert response.status_code == 404
        assert response.ok is False
        
        with pytest.raises(requests.exceptions.HTTPError):
            response.raise_for_status()
        
        session.close()
    
    def test_redirect_following_with_auth(self, base_url):
        """Test redirect following with authentication."""
        session = Session()
        session.auth = HTTPBasicAuth("user", "pass")
        
        response = session.get(f"{base_url}/redirect", allow_redirects=True)
        assert response.status_code == 200
        assert len(response.history) > 0
        
        session.close()