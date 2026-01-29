"""
HTTP-specific functionality.
"""
from typing import Optional, Dict, List, Tuple, Union, Any
import mitmproxy.flow


class HTTPRequest:
    """
    An HTTP request.
    """
    def __init__(
        self,
        host: str = "",
        port: int = 0,
        method: str = "GET",
        scheme: str = "http",
        authority: str = "",
        path: str = "",
        http_version: str = "HTTP/1.1",
        headers: Union[Dict[str, str], List[Tuple[str, str]]] = None,
        content: bytes = b"",
        trailers: Union[Dict[str, str], List[Tuple[str, str]]] = None,
        timestamp_start: float = 0,
        timestamp_end: float = 0,
    ):
        self.host = host
        self.port = port
        self.method = method
        self.scheme = scheme
        self.authority = authority
        self.path = path
        self.http_version = http_version
        self.headers = headers or {}
        self.content = content
        self.trailers = trailers or {}
        self.timestamp_start = timestamp_start
        self.timestamp_end = timestamp_end

    def copy(self):
        return HTTPRequest()

    @property
    def text(self) -> str:
        """The decoded content."""
        return self.content.decode("utf-8", "replace")

    @text.setter
    def text(self, text: str) -> None:
        self.content = text.encode("utf-8")

    @property
    def url(self) -> str:
        """
        The URL of this request.
        """
        return f"{self.scheme}://{self.host}:{self.port}{self.path}"


class HTTPResponse:
    """
    An HTTP response.
    """
    def __init__(
        self,
        http_version: str = "HTTP/1.1",
        status_code: int = 200,
        reason: str = "OK",
        headers: Union[Dict[str, str], List[Tuple[str, str]]] = None,
        content: bytes = b"",
        trailers: Union[Dict[str, str], List[Tuple[str, str]]] = None,
        timestamp_start: float = 0,
        timestamp_end: float = 0,
    ):
        self.http_version = http_version
        self.status_code = status_code
        self.reason = reason
        self.headers = headers or {}
        self.content = content
        self.trailers = trailers or {}
        self.timestamp_start = timestamp_start
        self.timestamp_end = timestamp_end

    def copy(self):
        return HTTPResponse()

    @property
    def text(self) -> str:
        """The decoded content."""
        return self.content.decode("utf-8", "replace")

    @text.setter
    def text(self, text: str) -> None:
        self.content = text.encode("utf-8")


class HTTPFlow(mitmproxy.flow.Flow):
    """
    An HTTP flow.
    """
    def __init__(self, client_conn=None, server_conn=None, live=None, mode="regular"):
        super().__init__()
        self.request: Optional[HTTPRequest] = None
        self.response: Optional[HTTPResponse] = None
        self.client_conn = client_conn
        self.server_conn = server_conn
        self.live = live
        self.mode = mode

    def copy(self):
        f = HTTPFlow()
        if self.request:
            f.request = self.request.copy()
        if self.response:
            f.response = self.response.copy()
        return f