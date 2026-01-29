from typing import Optional, Dict, Union, Tuple
from mitmproxy import flow

class Headers(dict):
    """
    A dictionary-like object for HTTP headers.
    """
    def __init__(self, fields: Union[Dict[str, str], list] = None, **kwargs):
        super().__init__()
        if fields:
            if isinstance(fields, dict):
                self.update(fields)
            elif isinstance(fields, list):
                for k, v in fields:
                    self[k] = v
        self.update(kwargs)

    def get_all(self, name):
        return [self.get(name)] if name in self else []

    def set_all(self, name, values):
        if values:
            self[name] = values[0]

    def add(self, name, value):
        # Simplified logic for mock
        self[name] = value

class Message:
    def __init__(self, content: bytes = b"", headers: Optional[Headers] = None):
        self.content = content
        self.headers = headers or Headers()
        self.timestamp_start = 0.0
        self.timestamp_end = 0.0
        self.http_version = "HTTP/1.1"

    def get_text(self, strict: bool = True) -> Optional[str]:
        return self.content.decode("utf-8", "replace")

    def set_text(self, text: str):
        self.content = text.encode("utf-8")

    text = property(get_text, set_text)

class Request(Message):
    def __init__(
        self,
        method: str = "GET",
        scheme: str = "http",
        host: str = "example.com",
        port: int = 80,
        path: str = "/",
        http_version: str = "HTTP/1.1",
        headers: Optional[Headers] = None,
        content: bytes = b"",
    ):
        super().__init__(content, headers)
        self.method = method
        self.scheme = scheme
        self.host = host
        self.port = port
        self.path = path
        self.http_version = http_version

    @property
    def url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}{self.path}"

    @url.setter
    def url(self, val: str):
        # Mock implementation
        pass

class Response(Message):
    def __init__(
        self,
        status_code: int = 200,
        headers: Optional[Headers] = None,
        content: bytes = b"",
        http_version: str = "HTTP/1.1",
    ):
        super().__init__(content, headers)
        self.status_code = status_code
        self.http_version = http_version
        self.reason = "OK"

class HTTPFlow(flow.Flow):
    """
    An HTTP Flow.
    """
    def __init__(self, client_conn, server_conn, live=None):
        super().__init__("http", client_conn, server_conn, live)
        self.request: Request = Request()
        self.response: Optional[Response] = None
        self.websocket = None