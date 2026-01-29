import json as _json
from urllib.parse import urlsplit, urlunsplit
from .utils import CaseInsensitiveDict, add_params_to_url, get_encoding_from_headers
from .exceptions import HTTPError
from .auth import HTTPBasicAuth


class Request:
    def __init__(self, method=None, url=None):
        self.method = method
        self.url = url
        self.headers = {}
        self.files = None
        self.data = None
        self.json = None
        self.params = None
        self.auth = None
        self.cookies = None

    def prepare(self):
        p = PreparedRequest()
        p.prepare(
            method=self.method,
            url=self.url,
            headers=self.headers,
            files=self.files,
            data=self.data,
            json=self.json,
            params=self.params,
            auth=self.auth,
            cookies=self.cookies,
        )
        return p


class PreparedRequest:
    def __init__(self):
        self.method = None
        self.url = None
        self.headers = CaseInsensitiveDict()
        self.body = None

    def prepare(
        self,
        method=None,
        url=None,
        headers=None,
        files=None,
        data=None,
        json=None,
        params=None,
        auth=None,
        cookies=None,
    ):
        self.prepare_method(method)
        self.prepare_url(url, params)
        self.prepare_headers(headers)
        self.prepare_auth(auth)
        self.prepare_body(data, json)
        self.prepare_cookies(cookies)

    def prepare_method(self, method):
        if method is None:
            raise ValueError("No method specified")
        self.method = method.upper()

    def prepare_url(self, url, params):
        if url is None:
            raise ValueError("Invalid URL: None")
        # accept URLs without scheme; default to http
        parts = urlsplit(url)
        if not parts.scheme:
            url = "http://" + url
        self.url = add_params_to_url(url, params)

    def prepare_headers(self, headers):
        self.headers = CaseInsensitiveDict()
        if headers:
            for k, v in headers.items():
                self.headers[k] = v

    def prepare_auth(self, auth):
        if auth is None:
            return
        if isinstance(auth, tuple) and len(auth) == 2:
            auth = HTTPBasicAuth(*auth)
        if hasattr(auth, "__call__"):
            auth(self)

    def prepare_body(self, data, json):
        body = None
        if json is not None:
            body = _json.dumps(json).encode("utf-8")
            if "Content-Type" not in self.headers:
                self.headers["Content-Type"] = "application/json"
        elif data is not None:
            if isinstance(data, (dict, list, tuple)):
                # default form-encoded
                from urllib.parse import urlencode
                body = urlencode(data, doseq=True).encode("utf-8")
                if "Content-Type" not in self.headers:
                    self.headers["Content-Type"] = "application/x-www-form-urlencoded"
            elif isinstance(data, bytes):
                body = data
            elif isinstance(data, str):
                body = data.encode("utf-8")
            else:
                # try coercion
                body = str(data).encode("utf-8")
        self.body = body
        if self.body is not None and "Content-Length" not in self.headers:
            self.headers["Content-Length"] = str(len(self.body))

    def prepare_cookies(self, cookies):
        if not cookies:
            return
        # cookies is a dict-like
        cookie_pairs = []
        for k, v in getattr(cookies, "items", lambda: cookies)():
            if isinstance(v, (list, tuple)):
                # pick first
                v = v[0]
            cookie_pairs.append(f"{k}={v}")
        if cookie_pairs:
            existing = self.headers.get("Cookie")
            cookie_header = "; ".join(cookie_pairs)
            if existing:
                cookie_header = existing + "; " + cookie_header
            self.headers["Cookie"] = cookie_header


class Response:
    def __init__(self):
        self.status_code = None
        self.headers = CaseInsensitiveDict()
        self._content = None
        self.url = None
        self.reason = None
        self.request = None
        self.history = []
        self.encoding = None
        self.cookies = None  # RequestsCookieJar-like

    @property
    def ok(self):
        return self.status_code is not None and self.status_code < 400

    @property
    def content(self):
        return self._content

    @property
    def text(self):
        enc = self.encoding or get_encoding_from_headers(self.headers) or "utf-8"
        try:
            return self.content.decode(enc, errors="replace")
        except LookupError:
            return self.content.decode("utf-8", errors="replace")

    def json(self, **kwargs):
        return _json.loads(self.text, **kwargs)

    def raise_for_status(self):
        if self.status_code is not None and 400 <= self.status_code:
            http_error_msg = f"{self.status_code} {self.reason or ''}"
            raise HTTPError(http_error_msg, response=self, request=self.request)