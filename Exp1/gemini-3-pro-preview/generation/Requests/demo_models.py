import requests
from requests import Request, Session
from server import BASE_URL

def run_demo():
    print("\n--- requests.models Demo ---")

    # 1. Constructing a Request manually
    # This is useful when you want to prepare a request but send it later,
    # or modify it slightly before sending.
    s = Session()
    
    url = f"{BASE_URL}/post"
    data = {'key': 'manual_preparation'}
    headers = {'User-Agent': 'Manual-Agent/1.0'}

    req = Request('POST', url, json=data, headers=headers)
    
    # 2. Preparing the Request
    # This converts the Request object into a PreparedRequest
    prepped = req.prepare()
    # Alternatively: prepped = s.prepare_request(req)
    
    print(f"Prepared Request URL: {prepped.url}")
    print(f"Prepared Request Headers: {prepped.headers}")
    print(f"Prepared Request Body: {prepped.body}")

    # 3. Sending the PreparedRequest
    print("Sending prepared request...")
    resp = s.send(prepped)
    
    print(f"Response Status: {resp.status_code}")
    print(f"Response Body: {resp.text}")
    
    # 4. Inspecting Response Object
    print(f"Response Encoding: {resp.encoding}")
    print(f"Response Elapsed Time: {resp.elapsed}")
    
    assert resp.status_code == 200
    assert resp.json()['data']['key'] == 'manual_preparation'