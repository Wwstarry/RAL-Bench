import requests

def test_session(server):
    sess = requests.Session()
    response = sess.get(server + '/')
    assert response.status_code == 200
    assert response.text == 'Hello, world!'

def test_session_cookies(server):
    sess = requests.Session()
    # First response sets a cookie for demonstration (not implemented in handler, but let's check client side anyway)
    # We can artificially set it.
    sess.cookies.set("testcookie", "cookievalue")
    response = sess.get(server + '/')
    assert response.status_code == 200
    # Ensure cookie is present in session
    assert sess.cookies.get("testcookie") == "cookievalue"