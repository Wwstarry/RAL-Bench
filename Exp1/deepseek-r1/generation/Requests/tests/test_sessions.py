import pytest
import requests

def test_session_persistence(httpbin):
    s = requests.Session()
    s.get(httpbin.url + "/cookies/set?sessioncookie=1234")
    response = s.get(httpbin.url + "/cookies")
    assert response.json()["cookies"]["sessioncookie"] == "1234"

def test_session_headers(httpbin):
    s = requests.Session()
    s.headers.update({"x-test": "true"})
    response = s.get(httpbin.url + "/headers")
    headers = response.json()["headers"]
    assert headers["X-Test"] == "true"

def test_session_cookies(httpbin):
    s = requests.Session()
    response = s.get(
        httpbin.url + "/cookies/set",
        cookies={"from-session": "value"},
        params={"name": "test", "value": "cookie"}
    )
    assert response.json()["cookies"]["test"] == "cookie"
    assert "from-session" in response.json()["cookies"]