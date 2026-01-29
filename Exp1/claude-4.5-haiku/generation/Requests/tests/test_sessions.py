import pytest
import requests
from requests.sessions import Session


class TestSessions:
    """Test Session lifecycle, cookies, and adapters."""
    
    def test_session_creation(self):
        """Test creating a session."""
        session = Session()
        assert session is not None
        assert isinstance(session, Session)
    
    def test_session_get_request(self, base_url):
        """Test GET request with session."""
        session = Session()
        response = session.get(f"{base_url}/get")
        assert response.status_code == 200
        session.close()
    
    def test_session_post_request(self, base_url):
        """Test POST request with session."""
        session = Session()
        response = session.post(f"{base_url}/post", json={"key": "value"})
        assert response.status_code == 200
        session.close()
    
    def test_session_cookies_persistence(self, base_url):
        """Test cookie persistence across requests."""
        session = Session()
        response1 = session.get(f"{base_url}/cookies")
        assert response1.status_code == 200
        
        assert "test_cookie" in session.cookies
        assert session.cookies["test_cookie"] == "test_value"
        session.close()
    
    def test_session_headers_persistence(self, base_url):
        """Test header persistence across requests."""
        session = Session()
        session.headers.update({"X-Session-Header": "persistent"})
        
        response = session.get(f"{base_url}/get")
        assert response.status_code == 200
        session.close()
    
    def test_session_context_manager(self, base_url):
        """Test session as context manager."""
        with Session() as session:
            response = session.get(f"{base_url}/get")
            assert response.status_code == 200
    
    def test_session_multiple_requests(self, base_url):
        """Test multiple requests with same session."""
        session = Session()
        
        response1 = session.get(f"{base_url}/get")
        assert response1.status_code == 200
        
        response2 = session.post(f"{base_url}/post", json={"data": "test"})
        assert response2.status_code == 200
        
        response3 = session.delete(f"{base_url}/delete")
        assert response3.status_code == 200
        
        session.close()
    
    def test_session_mount_adapter(self, base_url):
        """Test mounting custom adapter."""
        session = Session()
        adapter = requests.adapters.HTTPAdapter()
        session.mount("http://", adapter)
        
        response = session.get(f"{base_url}/get")
        assert response.status_code == 200
        session.close()
    
    def test_session_verify_ssl(self, base_url):
        """Test session with SSL verification setting."""
        session = Session()
        session.verify = False
        response = session.get(f"{base_url}/get")
        assert response.status_code == 200
        session.close()
    
    def test_session_timeout(self, base_url):
        """Test session request with timeout."""
        session = Session()
        response = session.get(f"{base_url}/get", timeout=5)
        assert response.status_code == 200
        session.close()