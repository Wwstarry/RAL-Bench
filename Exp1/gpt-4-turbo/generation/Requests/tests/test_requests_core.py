import threading
import time
import socket
import sys
import os

import requests
from requests import (
    get, post, put, delete, head, options, patch, request,
    Session, Request, PreparedRequest,
    HTTPError, ConnectionError, Timeout, TooManyRedirects, RequestException,
    Response
)
from requests.auth import HTTPBasicAuth
from requests.cookies import RequestsCookieJar

import http.server
import socketserver
import base64

import pytest

# --- Simple HTTP Server for Testing ---

class TestHandler(http.server.BaseHTTPRequestHandler):
    server_version = "TestHTTP/0.1"
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Hello, world!")
        elif self.path == "/cookies":
            cookie = self.headers.get("Cookie", "")
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(cookie.encode("utf-8"))
        elif self.path == "/auth":
            auth = self.headers.get("Authorization", "")
            if auth == "Basic " + base64.b64encode(b"user:pass").decode():
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"auth ok")
            else:
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="test"')
                self.end_headers()
        elif self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
        elif self.path == "/timeout":
            time.sleep(2)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"slow")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/echo":
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length)
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"put ok")

    def do_DELETE(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"delete ok")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, fmt, *args):
        # Silence server logs for test output
        pass

def find_free_port():
    s = socket.socket()
    s.bind(('', 0))
    addr, port = s.getsockname()
    s.close()
    return port

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

@pytest.fixture(scope="session")
def httpserver():
    port = find_free_port()
    server = ThreadedHTTPServer(("127.0.0.1", port), TestHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    url = f"http://127.0.0.1:{port}"
    yield url
    server.shutdown()
    thread.join()

# --- Tests ---

def test_get_basic(httpserver):
    r = get(httpserver + "/")
    assert r.status_code == 200
    assert r.text == "Hello, world!"

def test_post_echo(httpserver):
    payload = b"abc123"
    r = post(httpserver + "/echo", data=payload)
    assert r.status_code == 200
    assert r.content == payload

def test_put_delete_head_options_patch(httpserver):
    r = put(httpserver + "/")
    assert r.status_code == 200
    assert r.content == b"put ok"

    r = delete(httpserver + "/")
    assert r.status_code == 200
    assert r.content == b"delete ok"

    r = head(httpserver + "/")
    assert r.status_code == 200
    assert r.text == ""

    r = options(httpserver + "/")
    assert r.status_code in (200, 501)  # OPTIONS may not be implemented

    r = patch(httpserver + "/")
    assert r.status_code == 404  # PATCH not implemented

def test_request_api(httpserver):
    r = request("GET", httpserver + "/")
    assert r.ok
    r = request("POST", httpserver + "/echo", data="foo")
    assert r.text == "foo"

def test_session_cookies(httpserver):
    s = Session()
    # Set cookie
    s.cookies.set("a", "b")
    r = s.get(httpserver + "/cookies")
    assert "a=b" in r.text

    # Server sets cookie, client stores it
    s2 = Session()
    # Simulate server setting cookie
    class CookieHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Set-Cookie", "x=1")
            self.end_headers()
        def log_message(self, fmt, *args): pass
    port = find_free_port()
    server = ThreadedHTTPServer(("127.0.0.1", port), CookieHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    url = f"http://127.0.0.1:{port}"
    try:
        r = s2.get(url + "/")
        assert s2.cookies.get("x") == "1"
    finally:
        server.shutdown()
        thread.join()

def test_session_adapter_lifecycle(httpserver):
    s = Session()
    # Default adapter
    assert "http://" in s.adapters
    # Mount custom adapter (noop)
    class DummyAdapter(requests.adapters.HTTPAdapter):
        pass
    s.mount("http://test/", DummyAdapter())
    assert isinstance(s.get_adapter("http://test/"), DummyAdapter)
    s.close()

def test_models_request_response(httpserver):
    req = Request("POST", httpserver + "/echo", data="abc")
    preq = req.prepare()
    assert isinstance(preq, PreparedRequest)
    s = Session()
    resp = s.send(preq)
    assert isinstance(resp, Response)
    assert resp.text == "abc"

def test_auth_basic(httpserver):
    # Manual header
    auth = HTTPBasicAuth("user", "pass")
    r = get(httpserver + "/auth", auth=auth)
    assert r.status_code == 200
    assert r.text == "auth ok"

    # Wrong creds
    r = get(httpserver + "/auth", auth=("user", "wrong"))
    assert r.status_code == 401

def test_exceptions(httpserver):
    # ConnectionError
    with pytest.raises(ConnectionError):
        get("http://127.0.0.1:1/")  # unused port

    # Timeout
    with pytest.raises(Timeout):
        get(httpserver + "/timeout", timeout=0.5)

    # TooManyRedirects
    with pytest.raises(TooManyRedirects):
        get(httpserver + "/redirect", allow_redirects=True, max_redirects=1)

    # HTTPError
    r = get(httpserver + "/notfound")
    with pytest.raises(HTTPError):
        r.raise_for_status()

def test_response_content_attrs(httpserver):
    r = get(httpserver + "/")
    assert isinstance(r.content, bytes)
    assert isinstance(r.text, str)
    assert r.encoding is not None

def test_custom_headers(httpserver):
    r = get(httpserver + "/", headers={"X-Test": "abc"})
    assert r.status_code == 200

def test_streaming_response(httpserver):
    r = get(httpserver + "/", stream=True)
    data = b"".join(r.iter_content(2))
    assert data == b"Hello, world!"

def test_cookies_jar(httpserver):
    jar = RequestsCookieJar()
    jar.set("foo", "bar")
    r = get(httpserver + "/cookies", cookies=jar)
    assert "foo=bar" in r.text