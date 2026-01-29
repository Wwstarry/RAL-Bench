from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from .flow import Flow


class Headers:
    """
    Minimal case-insensitive headers container.

    Stores original-case key for round-trippable iteration, but lookups are
    case-insensitive.
    """

    def __init__(self, initial: Optional[Mapping[str, str]] = None):
        self._store: Dict[str, Tuple[str, str]] = {}
        if initial:
            for k, v in initial.items():
                self[k] = v

    def _norm(self, key: str) -> str:
        return key.lower()

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        nk = self._norm(key)
        if nk in self._store:
            return self._store[nk][1]
        return default

    def __getitem__(self, key: str) -> str:
        nk = self._norm(key)
        return self._store[nk][1]

    def __setitem__(self, key: str, value: str) -> None:
        nk = self._norm(key)
        self._store[nk] = (key, str(value))

    def __contains__(self, key: str) -> bool:
        return self._norm(key) in self._store

    def items(self) -> Iterable[Tuple[str, str]]:
        for _, (orig, val) in self._store.items():
            yield orig, val

    def to_dict(self) -> Dict[str, str]:
        return {orig: val for orig, val in self.items()}

    def get_state(self) -> Dict[str, str]:
        # JSON-serializable
        return self.to_dict()

    @classmethod
    def from_state(cls, state: Any) -> "Headers":
        if isinstance(state, dict):
            return cls(state)
        return cls()


@dataclass
class Message:
    http_version: str = "HTTP/1.1"
    headers: Headers = None  # type: ignore[assignment]
    content: bytes = b""
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None

    def __init__(
        self,
        *,
        http_version: str = "HTTP/1.1",
        headers: Optional[Mapping[str, str]] = None,
        content: bytes = b"",
    ):
        self.http_version = http_version
        self.headers = Headers(headers)
        self.content = content if isinstance(content, (bytes, bytearray)) else b""
        self.timestamp_start = None
        self.timestamp_end = None

    @property
    def text(self) -> str:
        return bytes(self.content).decode("utf-8", errors="replace")

    def set_text(self, text: str, encoding: str = "utf-8") -> None:
        self.content = (text or "").encode(encoding, errors="replace")

    @property
    def size(self) -> int:
        return len(self.content)

    def get_state(self) -> Dict[str, Any]:
        return {
            "http_version": self.http_version,
            "headers": self.headers.get_state(),
            "content": self.content,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        if not isinstance(state, dict):
            return
        if "http_version" in state and isinstance(state["http_version"], str):
            self.http_version = state["http_version"]
        if "headers" in state:
            self.headers = Headers.from_state(state.get("headers"))
        if "content" in state:
            c = state.get("content", b"")
            self.content = c if isinstance(c, (bytes, bytearray)) else b""
        if "timestamp_start" in state:
            self.timestamp_start = state.get("timestamp_start")
        if "timestamp_end" in state:
            self.timestamp_end = state.get("timestamp_end")


class Request(Message):
    method: str
    scheme: str
    host: str
    port: int
    path: str

    def __init__(
        self,
        *,
        method: str = "GET",
        scheme: str = "http",
        host: str = "",
        port: int = 80,
        path: str = "/",
        http_version: str = "HTTP/1.1",
        headers: Optional[Mapping[str, str]] = None,
        content: bytes = b"",
    ):
        super().__init__(http_version=http_version, headers=headers, content=content)
        self.method = method
        self.scheme = scheme
        self.host = host
        self.port = int(port)
        self.path = path

    @property
    def authority(self) -> str:
        if not self.host:
            return ""
        return f"{self.host}:{self.port}"

    @property
    def pretty_url(self) -> str:
        if not self.host:
            return self.path
        default_port = 80 if self.scheme == "http" else 443 if self.scheme == "https" else None
        if default_port is not None and self.port == default_port:
            return f"{self.scheme}://{self.host}{self.path}"
        return f"{self.scheme}://{self.host}:{self.port}{self.path}"


class Response(Message):
    status_code: int
    reason: str

    def __init__(
        self,
        *,
        status_code: int = 200,
        reason: str = "OK",
        http_version: str = "HTTP/1.1",
        headers: Optional[Mapping[str, str]] = None,
        content: bytes = b"",
    ):
        super().__init__(http_version=http_version, headers=headers, content=content)
        self.status_code = int(status_code)
        self.reason = reason

    def get_state(self) -> Dict[str, Any]:
        s = super().get_state()
        s.update({"status_code": self.status_code, "reason": self.reason})
        return s

    def set_state(self, state: Dict[str, Any]) -> None:
        super().set_state(state)
        if not isinstance(state, dict):
            return
        if "status_code" in state:
            try:
                self.status_code = int(state.get("status_code", 200))
            except Exception:
                self.status_code = 200
        if "reason" in state and isinstance(state["reason"], str):
            self.reason = state["reason"]


class HTTPFlow(Flow):
    request: Optional[Request]
    response: Optional[Response]
    websocket: Optional[object]
    client_conn: Optional[object]
    server_conn: Optional[object]

    def __init__(
        self,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
        id: Optional[str] = None,
    ):
        super().__init__(id=id, type="http")
        self.request = request
        self.response = response
        self.websocket = None
        self.client_conn = None
        self.server_conn = None

    def __repr__(self) -> str:
        if self.request:
            return f"<HTTPFlow id={self.id!r} {self.request.method} {self.request.pretty_url}>"
        return f"<HTTPFlow id={self.id!r} (no request)>"

    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        state["request"] = self.request.get_state() if self.request else None
        state["response"] = self.response.get_state() if self.response else None
        return state

    def set_state(self, state: Dict[str, Any]) -> None:
        super().set_state(state)
        if not isinstance(state, dict):
            return
        req_state = state.get("request")
        if isinstance(req_state, dict):
            req = Request()
            req.set_state(req_state)
            # set_state doesn't cover request-specific fields (method/scheme/host/port/path)
            # because they are not in Message. Handle here if provided.
            if "method" in req_state and isinstance(req_state["method"], str):
                req.method = req_state["method"]
            if "scheme" in req_state and isinstance(req_state["scheme"], str):
                req.scheme = req_state["scheme"]
            if "host" in req_state and isinstance(req_state["host"], str):
                req.host = req_state["host"]
            if "port" in req_state:
                try:
                    req.port = int(req_state.get("port", req.port))
                except Exception:
                    pass
            if "path" in req_state and isinstance(req_state["path"], str):
                req.path = req_state["path"]
            self.request = req
        else:
            self.request = None

        resp_state = state.get("response")
        if isinstance(resp_state, dict):
            resp = Response()
            resp.set_state(resp_state)
            self.response = resp
        else:
            self.response = None