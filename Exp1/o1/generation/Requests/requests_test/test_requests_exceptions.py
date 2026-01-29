import requests
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout

def test_http_error(server):
    # Using /status/404 to trigger HTTPError
    url = server + '/status/404'
    r = requests.get(url)
    assert r.status_code == 404
    try:
        r.raise_for_status()
    except HTTPError:
        pass
    else:
        assert False, "Expected HTTPError was not raised"

def test_connection_error():
    # Attempt to connect to non-listening port
    url = 'http://127.0.0.1:9999'
    try:
        requests.get(url, timeout=1)
    except ConnectionError:
        pass
    else:
        assert False, "Expected ConnectionError was not raised"

def test_timeout_error(server):
    # This server doesn't intentionally delay, but let's force a very short timeout to demonstrate
    try:
        requests.get(server + '/', timeout=0.0000001)
    except Timeout:
        pass
    except RequestException as e:
        # It's possible we get other socket-based exceptions first
        pass
    else:
        assert False, "Expected a timeout or request exception was not raised"