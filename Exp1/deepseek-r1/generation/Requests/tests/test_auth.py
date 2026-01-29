import pytest
import requests
from requests.auth import HTTPBasicAuth

def test_basic_auth_success(httpbin):
    auth = HTTPBasicAuth("user", "pass")
    response = requests.get(httpbin.url + "/basic-auth/user/pass", auth=auth)
    assert response.status_code == 200
    assert response.json()["authenticated"] is True

def test_basic_auth_failure(httpbin):
    auth = HTTPBasicAuth("wrong", "credentials")
    response = requests.get(httpbin.url + "/basic-auth/user/pass", auth=auth)
    assert response.status_code == 401