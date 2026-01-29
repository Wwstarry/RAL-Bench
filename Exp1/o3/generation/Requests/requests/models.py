"""
Very small subset of requests.models.Request / Response
"""
from __future__ import annotations

import json
import re
from typing import Optional

from .exceptions import HTTPError
from .utils import guess_json_utf, get_encoding_from_headers


class Request:
    def __init__(
        self, method: str, url: str, headers: Optional[dict] = None, body: bytes | None = None
    ):
        self.method = method.upper()
        self.url = url
        self.headers = headers or {}
        self.body = body

    def __repr__(self):  # pragma: no cover
        return f"<Request [{self.method}] {self.url}>"


class Response:
    """
    A simplified Response object that behaves *similarly* to requests.Response.
    """

    def __init__(self, *, url: str, status_code: int, headers: dict, content: bytes):
        self.url = url
        self.status_code = status_code
        self.headers = {k.title(): v for k, v in headers.items()}
        self._content = content
        self.encoding = get_encoding_from_headers(self.headers) or guess_json_utf(
            self._content
        ) or "utf-8"
        self.request: Optional[Request] = None

    # --- Properties ---------------------------------------------------------
    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    @property
    def text(self) -> str:
        return self._content.decode(self.encoding, errors="replace")

    @property
    def content(self) -> bytes:
        return self._content

    @property
    def reason(self) -> str:
        # Very naive extraction of reason phrase
        return (
            {
                200: "OK",
                201: "Created",
                202: "Accepted",
                204: "No Content",
                301: "Moved Permanently",
                302: "Found",
                400: "Bad Request",
                401: "Unauthorized",
                403: "Forbidden",
                404: "Not Found",
                500: "Internal Server Error",
            }.get(self.status_code, "")
            or ""
        )

    def json(self, **kwargs):
        """
        Deserialize response body as JSON text.
        """
        if not self._content:
            raise ValueError("No JSON object could be decoded")
        return json.loads(self.text, **kwargs)

    # --- Methods ------------------------------------------------------------
    def raise_for_status(self):
        """
        Raise HTTPError if the HTTP request returned an unsuccessful status code.
        """
        if not self.ok:
            raise HTTPError(f"{self.status_code} {self.reason}", response=self)

    def __repr__(self):  # pragma: no cover
        return f"<Response [{self.status_code}]>"