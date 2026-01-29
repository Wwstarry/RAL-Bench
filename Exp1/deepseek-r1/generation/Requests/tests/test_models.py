import pytest
import requests
from requests.models import Request, Response, PreparedRequest

def test_request_preparation(httpbin):
    req = Request('GET', httpbin.url + "/get", params={"key": "value"}).prepare()
    assert isinstance(req, PreparedRequest)
    assert "key=value" in req.url

def test_response_parsing(httpbin):
    response = requests.get(httpbin.url + "/get")
    assert response.status_code == 200
    assert response.url == httpbin.url + "/get"
    assert "application/json" in response.headers["Content-Type"]
    assert isinstance(response.json(), dict)

def test_response_redirect(httpbin):
    response = requests.get(httpbin.url + "/redirect-to?url=/get")
    assert response.status_code == 200
    assert response.url == httpbin.url + "/get"