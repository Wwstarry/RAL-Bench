import pytest
import requests
from requests.exceptions import RequestException

def test_get_request(httpbin):
    response = requests.get(httpbin.url + "/get")
    assert response.status_code == 200
    assert response.json()["url"] == httpbin.url + "/get"

def test_post_request(httpbin):
    data = {"key": "value"}
    response = requests.post(httpbin.url + "/post", data=data)
    assert response.status_code == 200
    assert response.json()["form"] == data

def test_put_request(httpbin):
    response = requests.put(httpbin.url + "/put", data={"key": "value"})
    assert response.status_code == 200

def test_delete_request(httpbin):
    response = requests.delete(httpbin.url + "/delete")
    assert response.status_code == 200

def test_head_request(httpbin):
    response = requests.head(httpbin.url + "/get")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"

def test_options_request(httpbin):
    response = requests.options(httpbin.url + "/get")
    assert response.status_code == 200
    assert "GET" in response.headers["Allow"]