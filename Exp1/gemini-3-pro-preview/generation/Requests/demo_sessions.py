import requests
from requests.adapters import HTTPAdapter
from server import BASE_URL

def run_demo():
    print("\n--- requests.sessions Demo ---")

    # 1. Session Lifecycle & Persistence
    # Sessions persist parameters (like headers) and cookies across requests
    s = requests.Session()
    s.headers.update({'x-test-header': 'persistent-value'})

    # 2. Cookie Persistence
    url_cookies = f"{BASE_URL}/cookies"
    
    # First request sets a cookie
    print(f"Session GET {url_cookies} (Setting cookie)")
    s.get(url_cookies, params={'set-name': 'session_id', 'set-value': '12345'})
    
    # Second request should send the cookie back automatically
    print(f"Session GET {url_cookies} (Checking cookie persistence)")
    resp = s.get(url_cookies)
    cookies_sent = resp.json().get('cookies', '')
    print(f"Server received cookies: {cookies_sent}")
    
    assert 'session_id=12345' in cookies_sent
    assert 'x-test-header' in resp.request.headers

    # 3. Adapters
    # Adapters allow defining connection behavior for specific prefixes
    print("\nMounting HTTPAdapter...")
    adapter = HTTPAdapter(max_retries=3)
    s.mount('http://', adapter)
    
    resp = s.get(f"{BASE_URL}/get")
    print(f"Request via adapter status: {resp.status_code}")
    
    s.close()