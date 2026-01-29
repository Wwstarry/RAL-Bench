import pytest
import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError

def test_timeout_exception(httpbin):
    with pytest.raises(Timeout):
        requests.get(httpbin.url + "/delay/3", timeout=1)

def test_connection_error():
    with pytest.raises(ConnectionError):
        requests.get("http://invalid.url")

def test_http_error_exception(httpbin):
    response = requests.get(httpbin.url + "/status/404")
    with pytest.raises(HTTPError):
        response.raise_for_status()