import pytest
import requests
from requests.auth import HTTPBasicAuth

class TestApi:
    """Tests for requests.api module"""

    def test_get(self, local_server):
        response = requests.get(local_server + "/")
        assert response.status_code == 200
        assert response.json() == {"message": "hello world"}

    def test_get_with_params(self, local_server):
        params = {"key1": "value1", "key2": ["value2a", "value2b"]}
        response = requests.get(local_server + "/params", params=params)
        assert response.status_code == 200
        assert response.json()["params"] == {"key1": ["value1"], "key2": ["value2a", "value2b"]}

    def test_post_form_data(self, local_server):
        data = {"key": "value"}
        response = requests.post(local_server + "/echo", data=data)
        assert response.status_code == 200
        assert "application/x-www-form-urlencoded" in response.json()["headers"]["Content-Type"]
        assert response.json()["body"] == "key=value"

    def test_post_json_data(self, local_server):
        json_data = {"key": "value"}
        response = requests.post(local_server + "/echo", json=json_data)
        assert response.status_code == 200
        assert "application/json" in response.json()["headers"]["Content-Type"]
        assert response.json()["json"] == json_data

    def test_put(self, local_server):
        json_data = {"update": "new_value"}
        response = requests.put(local_server + "/echo", json=json_data)
        assert response.status_code == 200
        assert response.json()["json"] == json_data

    def test_delete(self, local_server):
        response = requests.delete(local_server + "/delete")
        assert response.status_code == 200
        assert response.json() == {"status": "deleted"}

    def test_head(self, local_server):
        response = requests.head(local_server + "/")
        assert response.status_code == 200
        assert response.text == ""
        assert "Content-Length" in response.headers

    def test_options(self, local_server):
        response = requests.options(local_server + "/")
        assert response.status_code == 200
        assert "Allow" in response.headers
        assert "GET" in response.headers["Allow"]

    def test_custom_headers(self, local_server):
        headers = {"X-Custom-Header": "MyValue"}
        response = requests.get(local_server + "/headers", headers=headers)
        assert response.status_code == 200
        assert response.json()["headers"]["x-custom-header"] == "MyValue"


class TestSessions:
    """Tests for requests.sessions module"""

    def test_cookie_persistence(self, local_server):
        s = requests.Session()
        # First request sets the cookie
        response1 = s.get(local_server + "/cookies/set")
        assert response1.status_code == 200
        assert "test_cookie" in s.cookies

        # Second request should send the cookie back
        response2 = s.get(local_server + "/cookies/get")
        assert response2.status_code == 200
        assert response2.json() == {"status": "cookie received"}

    def test_session_isolation(self, local_server):
        s1 = requests.Session()
        s2 = requests.Session()

        # s1 gets a cookie
        s1.get(local_server + "/cookies/set")
        assert "test_cookie" in s1.cookies
        assert "test_cookie" not in s2.cookies

        # s2 makes a request, it should not have the cookie
        response = s2.get(local_server + "/cookies/get")
        assert response.status_code == 400
        assert response.json() == {"status": "cookie not found"}


class TestModels:
    """Tests for requests.models module"""

    def test_request_preparation(self, local_server):
        s = requests.Session()
        req = requests.Request(
            'GET',
            local_server + "/params",
            params={'foo': 'bar'},
            headers={'X-Test': 'true'}
        )
        
        prepped = s.prepare_request(req)

        assert isinstance(prepped, requests.PreparedRequest)
        assert prepped.method == 'GET'
        assert prepped.url == local_server + "/params?foo=bar"
        assert prepped.headers['X-Test'] == 'true'
        
        # Send the prepared request
        response = s.send(prepped)
        assert response.status_code == 200
        assert response.json()['params'] == {'foo': ['bar']}

    def test_response_object(self, local_server):
        response = requests.get(local_server + "/")
        
        assert response.status_code == 200
        assert response.reason == "OK"
        assert response.encoding == "utf-8"
        assert response.text == '{"message": "hello world"}'
        assert response.json() == {"message": "hello world"}
        assert "Content-Type" in response.headers
        assert "test_cookie" not in response.cookies

        # Test response with cookie
        response_with_cookie = requests.get(local_server + "/cookies/set")
        assert "test_cookie" in response_with_cookie.cookies
        assert response_with_cookie.cookies["test_cookie"] == "test_value"


class TestAuth:
    """Tests for requests.auth module"""

    def test_http_basic_auth_success(self, local_server):
        auth = HTTPBasicAuth('user', 'pass')
        response = requests.get(local_server + "/auth", auth=auth)
        assert response.status_code == 200
        assert response.json() == {"status": "auth successful"}

    def test_http_basic_auth_failure(self, local_server):
        auth = HTTPBasicAuth('user', 'wrongpass')
        response = requests.get(local_server + "/auth", auth=auth)
        assert response.status_code == 401

    def test_http_basic_auth_no_creds(self, local_server):
        response = requests.get(local_server + "/auth")
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers


class TestExceptions:
    """Tests for requests.exceptions"""

    def test_connection_error(self):
        # Assuming port 9999 is not in use
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.get("http://127.0.0.1:9999", timeout=0.1)

    def test_timeout(self, local_server):
        with pytest.raises(requests.exceptions.Timeout):
            requests.get(local_server + "/timeout", timeout=0.1)

    def test_http_error(self, local_server):
        response = requests.get(local_server + "/status/404")
        assert response.status_code == 404
        with pytest.raises(requests.exceptions.HTTPError) as excinfo:
            response.raise_for_status()
        assert "404 Client Error: Not Found for url" in str(excinfo.value)

        response = requests.get(local_server + "/status/500")
        assert response.status_code == 500
        with pytest.raises(requests.exceptions.HTTPError) as excinfo:
            response.raise_for_status()
        assert "500 Server Error: Internal Server Error for url" in str(excinfo.value)

    def test_too_many_redirects(self, local_server):
        s = requests.Session()
        s.max_redirects = 5
        with pytest.raises(requests.exceptions.TooManyRedirects):
            s.get(local_server + "/redirect/10")

    def test_default_redirect_behavior(self, local_server):
        # By default, requests allows redirects
        response = requests.get(local_server + "/redirect/2")
        assert response.status_code == 200
        assert response.json() == {"status": "redirect finished"}

    def test_disabling_redirects(self, local_server):
        response = requests.get(local_server + "/redirect/2", allow_redirects=False)
        assert response.status_code == 302
        assert response.is_redirect
        assert "/redirect/1" in response.headers['Location']