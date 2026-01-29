import requests

def test_api_get(server):
    r = requests.get(server + '/')
    assert r.status_code == 200
    assert r.text == 'Hello, world!'

def test_api_echo(server):
    msg = "test123"
    r = requests.get(server + '/echo', params={'msg': msg})
    assert r.status_code == 200
    assert r.text == f'Echo: {msg}'

def test_api_post(server):
    data = "some post data"
    r = requests.post(server + '/post', data=data)
    assert r.status_code == 200
    assert "Received: some post data" in r.text