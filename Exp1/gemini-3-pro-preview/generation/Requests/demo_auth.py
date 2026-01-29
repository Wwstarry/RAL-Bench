import requests
from requests.auth import HTTPBasicAuth
from server import BASE_URL

def run_demo():
    print("\n--- requests.auth Demo ---")

    user = "myuser"
    passwd = "mypassword"
    url = f"{BASE_URL}/basic-auth/{user}/{passwd}"

    # 1. Using HTTPBasicAuth explicitly
    print(f"GET {url} with HTTPBasicAuth")
    response = requests.get(url, auth=HTTPBasicAuth(user, passwd))
    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")
    assert response.status_code == 200
    assert response.json()['authenticated'] is True

    # 2. Using the tuple shortcut (Requests automatically maps tuples to HTTPBasicAuth)
    print(f"\nGET {url} with tuple auth")
    response = requests.get(url, auth=(user, passwd))
    print(f"Status: {response.status_code}")
    assert response.status_code == 200

    # 3. Failing Auth
    print(f"\nGET {url} with wrong password")
    response = requests.get(url, auth=(user, "wrong"))
    print(f"Status: {response.status_code}")
    assert response.status_code == 403