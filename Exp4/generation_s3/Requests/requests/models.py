from __future__ import annotations

import json as _json
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

from .exceptions import HTTPError, JSONDecodeError
from .structures import CaseInsensitiveDict


def _encode_params(params):
    if params is None:
        return ""
    if isinstance(params, (bytes, str)):
        return params.decode("utf-8") if isinstance(params, bytes) else params
    # dict or list of tuples
    return urlencode(params, doseq=True)


def _merge_params(url: str, params) -> str:
    if not params:
        return url
    split = urlsplit(url)
    existing = parse_qsl(split.query, keep_blank_values=True)
    new_params = []
    if isinstance(params, dict):
        for k, v in params.items():
            new_params.append((k, v))
    elif isinstance(params, (list, tuple)):
        # list of tuples
        new_params = list(params)
    else:
        # bytes/str; treat as query fragment
        enc = _encode_params(params)
        query = split.query
        if query:
            query = query + "&" + enc
        else:
            query = enc
        return urlunsplit((split.scheme, split.netloc, split.path, query, split.fragment))

    merged = existing + new_params
    query = urlencode(merged, doseq=True)
    return urlunsplit((split.scheme, split.netloc, split.path, query, split.fragment))


def _extract_charset(content_type: str | None) -> str | None:
    if not content_type:
        return None
    parts = [p.strip() for p in content_type.split(";")]
    for p in parts[1:]:
        if p.lower().startswith("charset="):
            return p.split("=", 1)[1].strip().strip('"')
    return None


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
        self.headers = headers or {}
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
        self.method = (method or "").upper()
        self.url = url
        self.headers = CaseInsensitiveDict(headers or {})

        # params onto url
        if self.url is not None:
            self.url = _merge_params(self.url, params)

        # body
        body = None
        if json is not None:
            body = _json.dumps(json).encode("utf-8")
            if self.headers.get("Content-Type") is None:
                self.headers["Content-Type"] = "application/json"
        elif isinstance(data, (dict, list, tuple)):
            # form encode
            body = urlencode(data, doseq=True).encode("utf-8")
            if self.headers.get("Content-Type") is None:
                self.headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif isinstance(data, str):
            body = data.encode("utf-8")
        elif isinstance(data, (bytes, bytearray)):
            body = bytes(data)
        else:
            body = None

        self.body = body
        # files ignored (minimal)


class Response:
    def __init__(self):
        self.status_code = 0
        self.headers = CaseInsensitiveDict()
        self.url = ""
        self.reason = None
        self.content = b""
        self.encoding = None
        self.request = None
        self.cookies = None
        self.history = []

    @property
    def ok(self):
        return 200 <= int(self.status_code) < 400

    @property
    def text(self):
        enc = self.encoding
        if not enc:
            enc = _extract_charset(self.headers.get("Content-Type")) or "utf-8"
        try:
            return self.content.decode(enc, errors="replace")
        except Exception:
            return self.content.decode("utf-8", errors="replace")

    def json(self):
        try:
            return _json.loads(self.text)
        except ValueError as e:
            raise JSONDecodeError(str(e)) from e

    def raise_for_status(self):
        if 400 <= int(self.status_code) < 600:
            reason = self.reason or ""
            msg = f"{self.status_code} {reason}".strip()
            raise HTTPError(msg)