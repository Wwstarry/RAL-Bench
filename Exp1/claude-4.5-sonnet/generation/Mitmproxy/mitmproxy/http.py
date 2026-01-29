"""
HTTP-specific flow types and message abstractions.
"""

from typing import Optional, Dict, List, Tuple
from mitmproxy.flow import Flow


class Message:
    """Base class for HTTP messages (requests and responses)."""
    
    def __init__(self):
        self.http_version: str = "HTTP/1.1"
        self.headers: Dict[str, str] = {}
        self.content: bytes = b""
        self.trailers: Optional[Dict[str, str]] = None
        self.timestamp_start: Optional[float] = None
        self.timestamp_end: Optional[float] = None


class Request(Message):
    """An HTTP request."""
    
    def __init__(self, 
                 host: str = "",
                 port: int = 80,
                 method: str = "GET",
                 scheme: str = "http",
                 authority: str = "",
                 path: str = "/"):
        super().__init__()
        self.host = host
        self.port = port
        self.method = method
        self.scheme = scheme
        self.authority = authority
        self.path = path
        
    @property
    def url(self) -> str:
        """The full URL string."""
        return f"{self.scheme}://{self.host}:{self.port}{self.path}"
        
    @property
    def pretty_url(self) -> str:
        """Like url, but omit the default port."""
        default_port = 443 if self.scheme == "https" else 80
        if self.port == default_port:
            return f"{self.scheme}://{self.host}{self.path}"
        return self.url


class Response(Message):
    """An HTTP response."""
    
    def __init__(self, 
                 status_code: int = 200,
                 reason: str = "OK"):
        super().__init__()
        self.status_code = status_code
        self.reason = reason


class HTTPFlow(Flow):
    """
    An HTTPFlow is a collection of objects representing a single HTTP transaction.
    """
    
    def __init__(self, client_conn=None, server_conn=None):
        super().__init__()
        self.request: Optional[Request] = None
        self.response: Optional[Response] = None
        self.client_conn = client_conn
        self.server_conn = server_conn
        self.websocket = None
        
    def copy(self) -> "HTTPFlow":
        """Create a copy of this HTTPFlow."""
        new_flow = HTTPFlow(self.client_conn, self.server_conn)
        new_flow.id = self.id
        new_flow.error = self.error
        new_flow.intercepted = self.intercepted
        new_flow.marked = self.marked
        new_flow.metadata = self.metadata.copy()
        new_flow.comment = self.comment
        new_flow.live = self.live
        
        if self.request:
            new_flow.request = Request(
                host=self.request.host,
                port=self.request.port,
                method=self.request.method,
                scheme=self.request.scheme,
                authority=self.request.authority,
                path=self.request.path
            )
            new_flow.request.headers = self.request.headers.copy()
            new_flow.request.content = self.request.content
            
        if self.response:
            new_flow.response = Response(
                status_code=self.response.status_code,
                reason=self.response.reason
            )
            new_flow.response.headers = self.response.headers.copy()
            new_flow.response.content = self.response.content
            
        return new_flow