# Minimal mitmproxy.http API surface

from typing import Optional, Dict, Any


class HTTPMessage:
    def __init__(self, headers: Optional[Dict[str, str]] = None, content: Optional[bytes] = None):
        self.headers = headers or {}
        self.content = content or b""


class Request(HTTPMessage):
    def __init__(
        self,
        method: str = "GET",
        scheme: str = "http",
        host: str = "localhost",
        port: int = 80,
        path: str = "/",
        http_version: str = "HTTP/1.1",
        headers: Optional[Dict[str, str]] = None,
        content: Optional[bytes] = None,
    ):
        super().__init__(headers, content)
        self.method = method
        self.scheme = scheme
        self.host = host
        self.port = port
        self.path = path
        self.http_version = http_version


class Response(HTTPMessage):
    def __init__(
        self,
        status_code: int = 200,
        reason: str = "OK",
        http_version: str = "HTTP/1.1",
        headers: Optional[Dict[str, str]] = None,
        content: Optional[bytes] = None,
    ):
        super().__init__(headers, content)
        self.status_code = status_code
        self.reason = reason
        self.http_version = http_version


class HTTPFlow:
    def __init__(
        self,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
        error: Optional[Any] = None,
    ):
        self.request = request or Request()
        self.response = response
        self.error = error

    def __repr__(self):
        return f"<HTTPFlow request={self.request.method} {self.request.path}>"