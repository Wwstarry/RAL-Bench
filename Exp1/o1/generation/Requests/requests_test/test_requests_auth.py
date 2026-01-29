import requests
from requests.auth import HTTPBasicAuth

def test_auth_correct(server):
    url = server + '/authenticated'
    r = requests.get(url, auth=HTTPBasicAuth('admin', 'secret'))
    assert r.status_code == 200
    assert r.text == 'Authenticated'

def test_auth_incorrect(server):
    url = server + '/authenticated'
    r = requests.get(url, auth=HTTPBasicAuth('wrong', 'credentials'))
    assert r.status_code == 401