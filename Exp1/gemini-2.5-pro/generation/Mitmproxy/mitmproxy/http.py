from mitmproxy import flow
from typing import List, Tuple, Optional, Union, Any

class Headers:
    """
    A stub for HTTP headers, providing a dict-like interface.
    """
    def __init__(self, fields: Optional[List[Tuple[bytes, bytes]]] = None):
        self._fields = fields if fields is not None else []

    def __getitem__(self, key: str) -> str:
        key = key.lower()
        for k, v in self._fields:
            if k.decode('utf-8', 'surrogateescape').lower() == key:
                return v.decode('utf-8', 'surrogateescape')
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        key = key.lower()
        for k, _ in self._fields:
            if k.decode('utf-8', 'surrogateescape').lower() == key:
                return True
        return False

    def get_all(self, key: str) -> List[str]:
        key = key.lower()
        return [
            v.decode('utf-8', 'surrogateescape')
            for k, v in self._fields
            if k.decode('utf-8', 'surrogateescape').lower() == key
        ]

    def __iter__(self):
        return iter(self._fields)

    def __len__(self):
        return len(self._fields)


class Message:
    """Base class for HTTP requests and responses."""
    def __init__(self):
        self.http_version: str = "HTTP/1.1"
        self.headers: Headers = Headers()
        self.content: Optional[bytes] = b""
        self.timestamp_start: float = 0.0
        self.timestamp_end: float = 0.0


class Request(Message):
    """A stub for an HTTP request."""
    def __init__(self):
        super().__init__()
        self.method: str = "GET"
        self.scheme: str = "https"
        self.host: str = "example.com"
        self.port: int = 443
        self.path: str = "/"


class Response(Message):
    """A stub for an HTTP response."""
    def __init__(self):
        super().__init__()
        self.status_code: int = 200
        self.reason: str = "OK"


class HTTPFlow(flow.Flow):
    """
    A stub for an HTTPFlow, which represents a single HTTP transaction.
    """
    def __init__(self):
        super().__init__()
        self.request: Request = Request()
        self.response: Optional[Response] = None
        self.error: Optional[Any] = None

    def __repr__(self):
        return f"<HTTPFlow {self.request.method} {self.request.host}{self.request.path}>"