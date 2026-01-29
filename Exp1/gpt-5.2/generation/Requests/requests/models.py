import json
from urllib.parse import urlsplit, urlunsplit, urlencode

from .exceptions import HTTPError


class CaseInsensitiveDict(dict):
    def __init__(self, data=None, **kwargs):
        super().__init__()
        if data:
            self.update(data)
        if kwargs:
            self.update(kwargs)

    def __setitem__(self, key, value):
        return super().__setitem__(key.lower(), value)

    def __getitem__(self, key):
        return super().__getitem__(key.lower())

    def get(self, key, default=None):
        return super().get(key.lower(), default)

    def __contains__(self, key):
        return super().__contains__(key.lower())

    def update(self, other=None, **kwargs):
        if other:
            if hasattr(other, "items"):
                for k, v in other.items():
                    super().__setitem__(str(k).lower(), v)
            else:
                for k, v in other:
                    super().__setitem__(str(k).lower(), v)
        for k, v in kwargs.items():
            super().__setitem__(str(k).lower(), v)


class Request:
    def __init__(
        self,
        method=None,
        url=None,
        headers=None,
        files=None,
        data=None,
        params=None,
        auth=None,
        cookies=None,
        json=None,
    ):
        self.method = method
        self.url = url
        self.headers = CaseInsensitiveDict(headers or {})
        self.files = files
        self.data = data
        self.params = params
        self.auth = auth
        self.cookies = cookies
        self.json = json

    def prepare(self):
        p = PreparedRequest()
        p.prepare(
            method=self.method,
            url=self.url,
            headers=self.headers,
            files=self.files,
            data=self.data,
            params=self.params,
            auth=self.auth,
            cookies=self.cookies,
            json=self.json,
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
        params=None,
        auth=None,
        cookies=None,
        json=None,
    ):
        self.prepare_method(method)
        self.prepare_url(url, params)
        self.prepare_headers(headers)
        self.prepare_body(data=data, json=json, files=files)
        if auth:
            auth(self)
        if cookies:
            # if cookies is dict, set Cookie header directly
            if isinstance(cookies, dict):
                cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
                if cookie_header:
                    self.headers["Cookie"] = cookie_header
        return self

    def prepare_method(self, method):
        self.method = (method or "").upper()
        return self

    def prepare_url(self, url, params):
        if not url:
            from .exceptions import URLRequired

            raise URLRequired("URL is required")
        parts = list(urlsplit(url))
        if not parts[0]:
            from .exceptions import MissingSchema

            raise MissingSchema(f"Invalid URL '{url}': No scheme supplied")
        if parts[0] not in ("http", "https"):
            from .exceptions import InvalidSchema

            raise InvalidSchema(f"Invalid URL '{url}': No connection adapters were found for '{url}'")
        if params:
            query = parts[3]
            q = []
            if query:
                from urllib.parse import parse_qsl

                q.extend(parse_qsl(query, keep_blank_values=True))
            if hasattr(params, "items"):
                items = list(params.items())
            else:
                items = list(params)
            q.extend(items)
            parts[3] = urlencode(q, doseq=True)
        self.url = urlunsplit(parts)
        return self

    def prepare_headers(self, headers):
        self.headers = CaseInsensitiveDict(headers or {})
        return self

    def prepare_body(self, data=None, json=None, files=None):
        body = None
        if json is not None:
            body = json_dumps(json)
            self.headers.setdefault("content-type", "application/json")
        elif data is not None:
            if isinstance(data, (bytes, bytearray)):
                body = bytes(data)
            elif isinstance(data, str):
                body = data.encode("utf-8")
            elif hasattr(data, "items"):
                body = urlencode(list(data.items()), doseq=True).encode("utf-8")
                self.headers.setdefault("content-type", "application/x-www-form-urlencoded")
            else:
                body = str(data).encode("utf-8")
        else:
            body = None
        self.body = body
        if body is not None and "content-length" not in self.headers:
            self.headers["content-length"] = str(len(body))
        return self


def json_dumps(obj):
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class Response:
    def __init__(self):
        self.status_code = None
        self.headers = CaseInsensitiveDict()
        self._content = b""
        self.url = None
        self.reason = None
        self.request = None
        self.history = []
        self.encoding = None

    @property
    def ok(self):
        return self.status_code is not None and 200 <= self.status_code < 400

    @property
    def content(self):
        return self._content or b""

    @property
    def text(self):
        enc = self.encoding
        if not enc:
            ct = self.headers.get("content-type")
            if ct and "charset=" in ct:
                enc = ct.split("charset=", 1)[1].split(";")[0].strip()
        if not enc:
            enc = "utf-8"
        return self.content.decode(enc, errors="replace")

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self):
        if self.status_code is None:
            return
        if 400 <= self.status_code:
            msg = f"{self.status_code} Server Error" if self.status_code >= 500 else f"{self.status_code} Client Error"
            raise HTTPError(msg, response=self)