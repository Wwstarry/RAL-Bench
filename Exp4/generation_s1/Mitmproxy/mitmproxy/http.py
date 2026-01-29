from __future__ import annotations

import copy
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union

from .flow import Flow


class Headers:
    """
    Minimal, case-insensitive header container with support for duplicate keys.
    Stores values as strings.
    """

    def __init__(self, fields: Optional[Union[List[Tuple[str, str]], Dict[str, str]]] = None):
        self._fields: List[Tuple[str, str]] = []
        if fields:
            if isinstance(fields, dict):
                for k, v in fields.items():
                    self.add(k, v)
            else:
                for k, v in fields:
                    self.add(k, v)

    @staticmethod
    def _norm(name: str) -> str:
        return name.lower()

    def add(self, name: str, value: str) -> None:
        self._fields.append((str(name), str(value)))

    def get_all(self, name: str) -> List[str]:
        n = self._norm(name)
        return [v for (k, v) in self._fields if self._norm(k) == n]

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        vals = self.get_all(name)
        return vals[-1] if vals else default

    def __getitem__(self, name: str) -> str:
        v = self.get(name)
        if v is None:
            raise KeyError(name)
        return v

    def __setitem__(self, name: str, value: str) -> None:
        n = self._norm(name)
        self._fields = [(k, v) for (k, v) in self._fields if self._norm(k) != n]
        self._fields.append((str(name), str(value)))

    def __contains__(self, name: str) -> bool:
        n = self._norm(name)
        return any(self._norm(k) == n for (k, v) in self._fields)

    def items(self, multi: bool = False) -> Iterator[Tuple[str, Union[str, List[str]]]]:
        if multi:
            # group by normalized name, preserving first-seen casing
            seen: Dict[str, Tuple[str, List[str]]] = {}
            order: List[str] = []
            for k, v in self._fields:
                nk = self._norm(k)
                if nk not in seen:
                    seen[nk] = (k, [v])
                    order.append(nk)
                else:
                    seen[nk][1].append(v)
            for nk in order:
                orig, vals = seen[nk]
                yield orig, vals
        else:
            for k, v in self._fields:
                yield k, v

    def __iter__(self) -> Iterable[str]:
        for k, _ in self._fields:
            yield k

    def __len__(self) -> int:
        return len(self._fields)

    def __repr__(self) -> str:
        return f"Headers({self._fields!r})"


class Message:
    def __init__(
        self,
        headers: Optional[Headers] = None,
        content: bytes = b"",
        timestamp_start: Optional[float] = None,
        timestamp_end: Optional[float] = None,
        trailers: Optional[Headers] = None,
    ):
        self.headers: Headers = headers if headers is not None else Headers()
        self.content: bytes = content if content is not None else b""
        self.timestamp_start: Optional[float] = timestamp_start
        self.timestamp_end: Optional[float] = timestamp_end
        self.trailers: Optional[Headers] = trailers

    @property
    def text(self) -> str:
        try:
            return self.content.decode("utf-8", errors="replace")
        except Exception:
            return str(self.content)


class Request(Message):
    def __init__(
        self,
        host: str = "example.com",
        port: int = 80,
        method: str = "GET",
        scheme: str = "http",
        path: str = "/",
        http_version: str = "HTTP/1.1",
        headers: Optional[Headers] = None,
        content: bytes = b"",
    ):
        super().__init__(headers=headers, content=content)
        self.host = host
        self.port = int(port)
        self.method = method
        self.scheme = scheme
        self.path = path
        self.http_version = http_version

    @property
    def pretty_url(self) -> str:
        default_port = 443 if self.scheme == "https" else 80
        hostport = self.host if self.port == default_port else f"{self.host}:{self.port}"
        p = self.path if self.path.startswith("/") else "/" + self.path
        return f"{self.scheme}://{hostport}{p}"


class Response(Message):
    def __init__(
        self,
        status_code: int = 200,
        reason: str = "OK",
        http_version: str = "HTTP/1.1",
        headers: Optional[Headers] = None,
        content: bytes = b"",
    ):
        super().__init__(headers=headers, content=content)
        self.status_code = int(status_code)
        self.reason = reason
        self.http_version = http_version


class HTTPFlow(Flow):
    def __init__(self, request: Optional[Request] = None):
        super().__init__()
        self.request: Optional[Request] = request
        self.response: Optional[Response] = None
        self.websocket: Optional[object] = None

    def get_state(self) -> Dict[str, Any]:
        s = super().get_state()
        s["request"] = None if self.request is None else _req_state(self.request)
        s["response"] = None if self.response is None else _resp_state(self.response)
        return s

    def set_state(self, state: Dict[str, Any]) -> None:
        super().set_state(state)
        rs = state.get("request", None)
        self.request = None if rs is None else _req_from_state(rs)
        ps = state.get("response", None)
        self.response = None if ps is None else _resp_from_state(ps)


def _headers_state(h: Headers) -> List[Tuple[str, str]]:
    return list(h.items(multi=False))


def _headers_from_state(fields: List[Tuple[str, str]]) -> Headers:
    return Headers(fields)


def _req_state(r: Request) -> Dict[str, Any]:
    return {
        "host": r.host,
        "port": r.port,
        "method": r.method,
        "scheme": r.scheme,
        "path": r.path,
        "http_version": r.http_version,
        "headers": _headers_state(r.headers),
        "content": r.content,
    }


def _resp_state(r: Response) -> Dict[str, Any]:
    return {
        "status_code": r.status_code,
        "reason": r.reason,
        "http_version": r.http_version,
        "headers": _headers_state(r.headers),
        "content": r.content,
    }


def _req_from_state(s: Dict[str, Any]) -> Request:
    return Request(
        host=s.get("host", "example.com"),
        port=s.get("port", 80),
        method=s.get("method", "GET"),
        scheme=s.get("scheme", "http"),
        path=s.get("path", "/"),
        http_version=s.get("http_version", "HTTP/1.1"),
        headers=_headers_from_state(s.get("headers", [])),
        content=s.get("content", b""),
    )


def _resp_from_state(s: Dict[str, Any]) -> Response:
    return Response(
        status_code=s.get("status_code", 200),
        reason=s.get("reason", "OK"),
        http_version=s.get("http_version", "HTTP/1.1"),
        headers=_headers_from_state(s.get("headers", [])),
        content=s.get("content", b""),
    )


__all__ = ["Headers", "Message", "Request", "Response", "HTTPFlow"]