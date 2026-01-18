import base64
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Tuple
from urllib.parse import parse_qs, urlparse


TARGET_ENV = "REQUESTS_TARGET"
ROOT_DIR = Path(__file__).resolve().parents[2]


def _looks_like_repo_root(repo_root: Path) -> bool:
    return (repo_root / "requests" / "__init__.py").exists()


def _select_repo_root() -> Path:
    override = os.environ.get("RACB_REPO_ROOT")
    if override:
        p = Path(override).resolve()
        if _looks_like_repo_root(p):
            return p

    target = os.environ.get(TARGET_ENV, "generated").lower()
    if target == "reference":
        return (ROOT_DIR / "repositories" / "requests").resolve()

    return (ROOT_DIR / "generation" / "Requests").resolve()


REPO_ROOT = _select_repo_root()
repo_str = str(REPO_ROOT)
if repo_str not in sys.path:
    sys.path.insert(0, repo_str)

import requests  # noqa: E402


def _new_session() -> requests.Session:
    """
    IMPORTANT: Disable environment proxy settings (HTTP_PROXY/HTTPS_PROXY/ALL_PROXY).
    The user's environment may route even localhost traffic through a proxy, which
    breaks deterministic local-server tests (502/timeout).
    """
    s = requests.Session()
    s.trust_env = False
    return s


class _TestHandler(BaseHTTPRequestHandler):
    server_version = "RACBTestHTTP/1.0"

    def log_message(self, fmt: str, *args) -> None:
        return

    def _send(self, code: int, body: bytes, content_type: str = "text/plain") -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/get":
            self._send(200, b"hello")
            return

        if path == "/json":
            body = json.dumps({"ok": True, "path": path}).encode("utf-8")
            self._send(200, body, content_type="application/json")
            return

        if path == "/echo-params":
            qs = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed.query).items()}
            body = json.dumps({"params": qs}).encode("utf-8")
            self._send(200, body, content_type="application/json")
            return

        if path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/get")
            self.end_headers()
            return

        if path == "/set-cookie":
            self.send_response(200)
            self.send_header("Set-Cookie", "session=abc123; Path=/")
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"cookie set")
            return

        if path == "/echo-cookie":
            cookie = self.headers.get("Cookie", "")
            body = json.dumps({"cookie": cookie}).encode("utf-8")
            self._send(200, body, content_type="application/json")
            return

        if path == "/basic-auth":
            auth = self.headers.get("Authorization", "")
            expected = "Basic " + base64.b64encode(b"user:pass").decode("ascii")
            if auth == expected:
                self._send(200, b"ok")
            else:
                self._send(401, b"unauthorized")
            return

        if path == "/slow":
            time.sleep(0.05)
            self._send(200, b"slow ok")
            return

        self._send(404, b"not found")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b""

        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype == "application/json":
            data = json.loads(raw.decode("utf-8") or "{}")
        else:
            form = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(raw.decode("utf-8")).items()}
            data = form

        body = json.dumps({"path": path, "data": data}).encode("utf-8")
        self._send(200, body, content_type="application/json")


def _start_server() -> Tuple[HTTPServer, str]:
    httpd = HTTPServer(("127.0.0.1", 0), _TestHandler)
    host, port = httpd.server_address
    base_url = f"http://{host}:{port}"

    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, base_url


def test_get_text_response() -> None:
    httpd, base_url = _start_server()
    s = _new_session()
    try:
        r = s.get(base_url + "/get")
        assert r.status_code == 200
        assert r.text == "hello"
    finally:
        s.close()
        httpd.shutdown()
        httpd.server_close()


def test_get_with_query_params() -> None:
    httpd, base_url = _start_server()
    s = _new_session()
    try:
        r = s.get(base_url + "/echo-params", params={"a": "1", "b": "two"})
        assert r.status_code == 200
        payload = r.json()
        assert payload["params"]["a"] == "1"
        assert payload["params"]["b"] == "two"
    finally:
        s.close()
        httpd.shutdown()
        httpd.server_close()


def test_post_form_data() -> None:
    httpd, base_url = _start_server()
    s = _new_session()
    try:
        r = s.post(base_url + "/submit", data={"x": "10", "y": "20"})
        assert r.status_code == 200
        payload = r.json()
        assert payload["path"] == "/submit"
        assert payload["data"]["x"] == "10"
        assert payload["data"]["y"] == "20"
    finally:
        s.close()
        httpd.shutdown()
        httpd.server_close()


def test_post_json_data() -> None:
    httpd, base_url = _start_server()
    s = _new_session()
    try:
        r = s.post(base_url + "/json-submit", json={"ok": True, "n": 3})
        assert r.status_code == 200
        payload = r.json()
        assert payload["path"] == "/json-submit"
        assert payload["data"]["ok"] is True
        assert payload["data"]["n"] == 3
    finally:
        s.close()
        httpd.shutdown()
        httpd.server_close()


def test_redirect_is_followed_by_default() -> None:
    httpd, base_url = _start_server()
    s = _new_session()
    try:
        r = s.get(base_url + "/redirect")
        assert r.status_code == 200
        assert r.url.endswith("/get")
        assert r.text == "hello"
    finally:
        s.close()
        httpd.shutdown()
        httpd.server_close()


def test_session_persists_cookies() -> None:
    httpd, base_url = _start_server()
    s = _new_session()
    try:
        r1 = s.get(base_url + "/set-cookie")
        assert r1.status_code == 200

        r2 = s.get(base_url + "/echo-cookie")
        assert r2.status_code == 200
        payload = r2.json()
        assert "session=abc123" in payload["cookie"]
    finally:
        s.close()
        httpd.shutdown()
        httpd.server_close()


def test_basic_auth_success() -> None:
    httpd, base_url = _start_server()
    s = _new_session()
    try:
        r = s.get(base_url + "/basic-auth", auth=("user", "pass"))
        assert r.status_code == 200
        assert r.text == "ok"
    finally:
        s.close()
        httpd.shutdown()
        httpd.server_close()


def test_streaming_response_iter_content() -> None:
    httpd, base_url = _start_server()
    s = _new_session()
    try:
        r = s.get(base_url + "/get", stream=True)
        assert r.status_code == 200
        chunks = list(r.iter_content(chunk_size=2))
        assert b"".join(chunks) == b"hello"
    finally:
        s.close()
        httpd.shutdown()
        httpd.server_close()


def test_timeout_parameter_on_fast_endpoint() -> None:
    httpd, base_url = _start_server()
    s = _new_session()
    try:
        r = s.get(base_url + "/slow", timeout=1.0)
        assert r.status_code == 200
        assert r.text == "slow ok"
    finally:
        s.close()
        httpd.shutdown()
        httpd.server_close()


def test_prepared_request_contains_headers_and_url() -> None:
    httpd, base_url = _start_server()
    s = _new_session()
    try:
        req = requests.Request("GET", base_url + "/get", headers={"X-Test": "1"})
        prepped = s.prepare_request(req)
        assert prepped.method == "GET"
        assert prepped.url.endswith("/get")
        assert prepped.headers["X-Test"] == "1"
    finally:
        s.close()
        httpd.shutdown()
        httpd.server_close()
