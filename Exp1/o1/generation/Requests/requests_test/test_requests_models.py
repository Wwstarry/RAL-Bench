import requests
from requests import Request, Session

def test_models_request_preparation(server):
    url = server + '/echo'
    params = {'msg': 'prepped'}
    req = Request('GET', url, params=params)
    prepped = req.prepare()

    s = Session()
    resp = s.send(prepped)
    assert resp.status_code == 200
    assert resp.text == 'Echo: prepped'

def test_models_response_attributes(server):
    r = requests.get(server + '/')
    assert r.status_code == 200
    assert r.ok
    assert r.text == 'Hello, world!'
    assert r.headers is not None