import requests
from server import BASE_URL

def run_demo():
    print("\n--- requests.api Demo ---")
    
    # 1. GET Request
    url_get = f"{BASE_URL}/get"
    params = {'key1': 'value1', 'key2': 'value2'}
    print(f"GET {url_get} with params {params}")
    response = requests.get(url_get, params=params)
    print(f"Status: {response.status_code}")
    print(f"Response JSON: {response.json()}")
    assert response.status_code == 200
    assert response.json()['args']['key1'] == 'value1'

    # 2. POST Request
    url_post = f"{BASE_URL}/post"
    payload = {'user': 'admin', 'active': True}
    print(f"\nPOST {url_post} with json {payload}")
    response = requests.post(url_post, json=payload)
    print(f"Status: {response.status_code}")
    data_received = response.json()['data']
    print(f"Server received data: {data_received}")
    assert data_received['user'] == 'admin'

    # 3. PUT Request
    url_put = f"{BASE_URL}/put"
    print(f"\nPUT {url_put}")
    response = requests.put(url_put, data="raw string data")
    print(f"Status: {response.status_code}")
    assert response.json()['method'] == 'PUT'

    # 4. DELETE Request
    url_delete = f"{BASE_URL}/delete"
    print(f"\nDELETE {url_delete}")
    response = requests.delete(url_delete)
    print(f"Status: {response.status_code}")
    assert response.json()['method'] == 'DELETE'