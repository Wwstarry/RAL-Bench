import pytest
import requests
from requests.exceptions import (
    RequestException,
    ConnectionError,
    HTTPError,
    URLRequired,
    TooManyRedirects,
    Timeout,
    InvalidURL,
)


class TestExceptions:
    """Test request error taxonomy."""
    
    def test_request_exception_base(self):
        """Test RequestException is base class."""
        exc = RequestException("test error")
        assert isinstance(exc, Exception)
    
    def test_connection_error_inheritance(self):
        """Test ConnectionError inherits from RequestException."""
        exc = ConnectionError("connection failed")
        assert isinstance(exc, RequestException)
    
    def test_http_error_inheritance(self):
        """Test HTTPError inherits from RequestException."""
        exc = HTTPError("http error")
        assert isinstance(exc, RequestException)
    
    def test_timeout_error_inheritance(self):
        """Test Timeout inherits from RequestException."""
        exc = Timeout("timeout")
        assert isinstance(exc, RequestException)
    
    def test_too_many_redirects_inheritance(self):
        """Test TooManyRedirects inherits from RequestException."""
        exc = TooManyRedirects("too many redirects")
        assert isinstance(exc, RequestException)
    
    def test_url_required_inheritance(self):
        """Test URLRequired inherits from RequestException."""
        exc = URLRequired("url required")
        assert isinstance(exc, RequestException)
    
    def test_invalid_url_inheritance(self):
        """Test InvalidURL inherits from RequestException."""
        exc = InvalidURL("invalid url")
        assert isinstance(exc, RequestException)
    
    def test_exception_message(self):
        """Test exception message."""
        msg = "test error message"
        exc = RequestException(msg)
        assert str(exc) == msg
    
    def test_http_error_with_response(self, base_url):
        """Test HTTPError with response object."""
        response = requests.get(f"{base_url}/status/404")
        try:
            response.raise_for_status()
            assert False, "Should have raised HTTPError"
        except HTTPError as e:
            assert e.response.status_code == 404
    
    def test_raise_for_status_success(self, base_url):
        """Test raise_for_status on success."""
        response = requests.get(f"{base_url}/status/200")
        response.raise_for_status()
    
    def test_raise_for_status_failure(self, base_url):
        """Test raise_for_status on failure."""
        response = requests.get(f"{base_url}/status/500")
        with pytest.raises(HTTPError):
            response.raise_for_status()
    
    def test_invalid_url_exception(self):
        """Test InvalidURL exception."""
        with pytest.raises(InvalidURL):
            requests.get("not a valid url")