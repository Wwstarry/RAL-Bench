from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Union

from .flow import Flow


Headers = Dict[str, str]


@dataclass
class Message:
    headers: Headers = field(default_factory=dict)
    content: bytes = b""
    http_version: str = "HTTP/1.1"

    @property
    def text(self) -> str:
        try:
            return self.content.decode("utf-8", errors="replace")
        except Exception:
            return ""

    @text.setter
    def text(self, value: str) -> None:
        self.content = value.encode("utf-8")


@dataclass
class Request(Message):
    method: str = "GET"
    scheme: str = "http"
    host: str = "example.com"
    port: int = 80
    path: str = "/"

    @property
    def url(self) -> str:
        default_port = 443 if self.scheme == "https" else 80
        hostport = self.host if self.port == default_port else f"{self.host}:{self.port}"
        return f"{self.scheme}://{hostport}{self.path}"


@dataclass
class Response(Message):
    status_code: int = 200
    reason: str = "OK"


@dataclass
class HTTPFlow(Flow):
    """
    Minimal HTTPFlow compatible with mitmproxy.http.HTTPFlow.
    """
    type: str = "http"
    request: Optional[Request] = None
    response: Optional[Response] = None

    def __post_init__(self) -> None:
        # In real mitmproxy these are always present, but tests may create empty flows.
        if self.request is None:
            self.request = Request()
        if self.response is None:
            self.response = None


HTTPMessage = Union[Request, Response, Message]