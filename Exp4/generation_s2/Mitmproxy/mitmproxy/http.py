from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, Union

from mitmproxy.flow import Flow


HeadersLike = Union[
    Mapping[str, str],
    Mapping[bytes, bytes],
    Iterable[Tuple[str, str]],
    Iterable[Tuple[bytes, bytes]],
    None,
]


def _normalize_headers(headers: HeadersLike) -> List[Tuple[bytes, bytes]]:
    if headers is None:
        return []
    if isinstance(headers, dict):
        items = list(headers.items())
    else:
        items = list(headers)
    out: List[Tuple[bytes, bytes]] = []
    for k, v in items:
        kb = k if isinstance(k, (bytes, bytearray)) else str(k).encode("utf-8", "surrogatepass")
        vb = v if isinstance(v, (bytes, bytearray)) else str(v).encode("utf-8", "surrogatepass")
        out.append((bytes(kb), bytes(vb)))
    return out


@dataclass
class Headers:
    """
    Very small header container.

    Real mitmproxy has a full multi-dict with case-insensitive lookups.
    For test compatibility, we provide basic iteration and get/set behavior.
    """
    fields: List[Tuple[bytes, bytes]] = field(default_factory=list)

    @classmethod
    def from_items(cls, headers: HeadersLike = None) -> "Headers":
        return cls(_normalize_headers(headers))

    def items(self) -> List[Tuple[bytes, bytes]]:
        return list(self.fields)

    def get(self, key: Union[str, bytes], default: Optional[str] = None) -> Optional[str]:
        kb = key if isinstance(key, (bytes, bytearray)) else str(key).encode("utf-8", "surrogatepass")
        kb = bytes(kb).lower()
        for k, v in self.fields:
            if k.lower() == kb:
                try:
                    return v.decode("utf-8", "replace")
                except Exception:
                    return repr(v)
        return default

    def __contains__(self, key: Union[str, bytes]) -> bool:
        return self.get(key, None) is not None

    def __iter__(self):
        return iter(self.fields)

    def __len__(self) -> int:
        return len(self.fields)

    def __setitem__(self, key: Union[str, bytes], value: Union[str, bytes]) -> None:
        kb = key if isinstance(key, (bytes, bytearray)) else str(key).encode("utf-8", "surrogatepass")
        vb = value if isinstance(value, (bytes, bytearray)) else str(value).encode("utf-8", "surrogatepass")
        kb_l = bytes(kb).lower()
        # remove existing
        self.fields = [(k, v) for (k, v) in self.fields if k.lower() != kb_l]
        self.fields.append((bytes(kb), bytes(vb)))

    def __getitem__(self, key: Union[str, bytes]) -> str:
        v = self.get(key)
        if v is None:
            raise KeyError(key)
        return v


@dataclass
class Message:
    headers: Headers = field(default_factory=Headers)
    content: bytes = b""
    trailers: Headers = field(default_factory=Headers)
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None

    @property
    def text(self) -> str:
        try:
            return self.content.decode("utf-8")
        except Exception:
            return self.content.decode("utf-8", "replace")

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
    http_version: str = "HTTP/1.1"

    @property
    def url(self) -> str:
        default_port = 443 if self.scheme == "https" else 80
        hostport = self.host
        if self.port != default_port:
            hostport = f"{self.host}:{self.port}"
        return f"{self.scheme}://{hostport}{self.path}"


@dataclass
class Response(Message):
    status_code: int = 200
    reason: str = "OK"
    http_version: str = "HTTP/1.1"


@dataclass
class HTTPFlow(Flow):
    request: Optional[Request] = None
    response: Optional[Response] = None

    def __repr__(self) -> str:
        if self.request:
            return f"<HTTPFlow {self.request.method} {self.request.url}>"
        return "<HTTPFlow (no request)>"

    @property
    def live(self) -> bool:
        # Keep compatibility with Flow.live attribute but derived from metadata if present.
        return bool(self.metadata.get("live", False))

    @live.setter
    def live(self, value: bool) -> None:
        self.metadata["live"] = bool(value)


def make_request(
    method: str = "GET",
    url: str = "http://example.com/",
    headers: HeadersLike = None,
    content: bytes = b"",
) -> Request:
    """
    Convenience helper for tests: create a Request from a URL.
    Very small URL parsing that avoids external dependencies.
    """
    scheme = "http"
    rest = url
    if "://" in url:
        scheme, rest = url.split("://", 1)
    hostport, _, path = rest.partition("/")
    path = "/" + path if path else "/"
    host = hostport
    port = 443 if scheme == "https" else 80
    if ":" in hostport:
        host, p = hostport.rsplit(":", 1)
        try:
            port = int(p)
        except ValueError:
            port = 443 if scheme == "https" else 80
    req = Request(
        method=method,
        scheme=scheme,
        host=host,
        port=port,
        path=path,
        headers=Headers.from_items(headers),
        content=content,
    )
    return req


def make_response(
    status_code: int = 200,
    content: bytes = b"",
    headers: HeadersLike = None,
    reason: str = "OK",
) -> Response:
    return Response(
        status_code=status_code,
        reason=reason,
        headers=Headers.from_items(headers),
        content=content,
    )