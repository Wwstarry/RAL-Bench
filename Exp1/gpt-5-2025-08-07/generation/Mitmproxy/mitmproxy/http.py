"""
Minimal HTTP message and flow types.

This module provides simplified HTTP request/response types and HTTPFlow,
sufficient for importability and basic addon usage in a safe, no-I/O environment.
"""

from __future__ import annotations

from typing import Iterable, Iterator, List, Optional, Tuple
from .flow import Flow


class Headers:
    """
    Simple HTTP headers container.

    Internally stored as a list of (name, value) tuples to preserve order and allow duplicates.
    Header name comparisons are case-insensitive.
    """

    def __init__(self, fields: Optional[Iterable[Tuple[str, str]]] = None) -> None:
        self._headers: List[Tuple[str, str]] = []
        if fields:
            for k, v in fields:
                self.add(k, v)

    def add(self, name: str, value: str) -> None:
        self._headers.append((str(name), str(value)))

    def get_all(self, name: str) -> List[str]:
        n = name.lower()
        return [v for k, v in self._headers if k.lower() == n]

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        vals = self.get_all(name)
        return vals[0] if vals else default

    def __getitem__(self, name: str) -> str:
        v = self.get(name)
        if v is None:
            raise KeyError(name)
        return v

    def __setitem__(self, name: str, value: str) -> None:
        n = name.lower()
        # replace existing occurrences
        kept: List[Tuple[str, str]] = [(k, v) for (k, v) in self._headers if k.lower() != n]
        kept.append((name, value))
        self._headers = kept

    def __contains__(self, name: str) -> bool:
        return self.get(name) is not None

    def items(self) -> Iterator[Tuple[str, str]]:
        return iter(self._headers)

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        return self.items()

    def __len__(self) -> int:
        return len(self._headers)

    def copy(self) -> "Headers":
        return Headers(self._headers)


class Message:
    """
    Minimal HTTP message base type with headers and content.
    """

    def __init__(
        self,
        http_version: str = "HTTP/1.1",
        headers: Optional[Headers] = None,
        content: Optional[bytes] = None,
    ) -> None:
        self.http_version: str = http_version
        self.headers: Headers = headers if headers is not None else Headers()
        self.content: bytes = content if content is not None else b""

    def get_text(self, encoding: str = "utf-8", errors: str = "replace") -> str:
        return self.content.decode(encoding, errors)

    def set_text(self, text: str, encoding: str = "utf-8") -> None:
        self.content = text.encode(encoding)


class Request(Message):
    """
    Minimal HTTP request.
    """

    def __init__(
        self,
        method: str = "GET",
        scheme: str = "http",
        host: str = "localhost",
        port: int = 80,
        path: str = "/",
        http_version: str = "HTTP/1.1",
        headers: Optional[Headers] = None,
        content: Optional[bytes] = None,
    ) -> None:
        super().__init__(http_version=http_version, headers=headers, content=content)
        self.method: str = method
        self.scheme: str = scheme
        self.host: str = host
        self.port: int = int(port)
        self.path: str = path

    @property
    def authority(self) -> str:
        return f"{self.host}:{self.port}"

    @property
    def url(self) -> str:
        return f"{self.scheme}://{self.authority}{self.path}"

    def __repr__(self) -> str:
        return f"<Request {self.method} {self.url}>"


class Response(Message):
    """
    Minimal HTTP response.
    """

    def __init__(
        self,
        status_code: int = 200,
        reason: str = "OK",
        http_version: str = "HTTP/1.1",
        headers: Optional[Headers] = None,
        content: Optional[bytes] = None,
    ) -> None:
        super().__init__(http_version=http_version, headers=headers, content=content)
        self.status_code: int = int(status_code)
        self.reason: str = reason

    def __repr__(self) -> str:
        return f"<Response {self.status_code} {self.reason}>"


class HTTPFlow(Flow):
    """
    Minimal HTTP flow with optional request/response.

    Attributes:
        request: Request instance.
        response: Response instance, may be None until set.
        error: Optional error description string for failed flows.
    """

    def __init__(self) -> None:
        super().__init__(flow_type="http")
        self.request: Optional[Request] = None
        self.response: Optional[Response] = None
        self.error: Optional[str] = None

    def __repr__(self) -> str:
        if self.request:
            return f"<HTTPFlow id={self.id} {self.request.method} {self.request.path}>"
        return f"<HTTPFlow id={self.id}>"