import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError
from server import BASE_URL

def run_demo():
    print("\n--- requests.exceptions Demo ---")

    # 1. HTTPError (raise_for_status)
    print("Testing raise_for_status() with 500 error...")
    url_500 = f"{BASE_URL}/status/500"
    resp = requests.get(url_500)
    try:
        resp.raise_for_status()
    except HTTPError as e:
        print(f"Caught expected HTTPError: {e}")

    # 2. Timeout
    # The server sleeps for 2 seconds at /timeout
    print("\nTesting ReadTimeout...")
    url_timeout = f"{BASE_URL}/timeout"
    try:
        requests.get(url_timeout, timeout=0.5)
    except Timeout as e:
        print(f"Caught expected Timeout: {e}")

    # 3. ConnectionError
    # Connecting to a port where no server is running
    print("\nTesting ConnectionError...")
    bad_port_url = "http://localhost:9999"
    try:
        requests.get(bad_port_url)
    except ConnectionError as e:
        print(f"Caught expected ConnectionError: {e}")