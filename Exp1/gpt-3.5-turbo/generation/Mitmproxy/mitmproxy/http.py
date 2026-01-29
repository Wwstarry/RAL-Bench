from typing import Optional


class HTTPMessage:
    def __init__(self, headers=None, content: bytes = b""):
        self.headers = headers or {}
        self.content = content

    def get_header(self, name: str) -> Optional[str]:
        return self.headers.get(name.lower())

    def set_header(self, name: str, value: str) -> None:
        self.headers[name.lower()] = value


class HTTPRequest(HTTPMessage):
    def __init__(self, method: str = "GET", scheme: str = "http", host: str = "", port: int = 80,
                 path: str = "/", http_version: str = "HTTP/1.1", headers=None, content: bytes = b""):
        super().__init__(headers, content)
        self.method = method
        self.scheme = scheme
        self.host = host
        self.port = port
        self.path = path
        self.http_version = http_version


class HTTPResponse(HTTPMessage):
    def __init__(self, status_code: int = 200, reason: str = "OK", http_version: str = "HTTP/1.1",
                 headers=None, content: bytes = b""):
        super().__init__(headers, content)
        self.status_code = status_code
        self.reason = reason
        self.http_version = http_version


class HTTPFlow:
    def __init__(self, request: Optional[HTTPRequest] = None, response: Optional[HTTPResponse] = None):
        self.request = request or HTTPRequest()
        self.response = response or HTTPResponse()