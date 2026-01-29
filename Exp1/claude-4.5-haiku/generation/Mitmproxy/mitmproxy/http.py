"""
HTTP flow and message types for mitmproxy.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from mitmproxy.flow import Flow, Request, Response, FlowType


@dataclass
class HTTPRequest(Request):
    """
    HTTP request message.
    """
    method: str = "GET"
    scheme: str = "http"
    authority: str = "example.com"
    path: str = "/"
    http_version: str = "HTTP/1.1"
    headers: Dict[str, str] = field(default_factory=dict)
    content: bytes = b""
    trailers: Optional[Dict[str, str]] = None
    timestamp_start: float = 0.0
    timestamp_end: float = 0.0


@dataclass
class HTTPResponse(Response):
    """
    HTTP response message.
    """
    http_version: str = "HTTP/1.1"
    status_code: int = 200
    reason: str = "OK"
    headers: Dict[str, str] = field(default_factory=dict)
    content: bytes = b""
    trailers: Optional[Dict[str, str]] = None
    timestamp_start: float = 0.0
    timestamp_end: float = 0.0


@dataclass
class HTTPFlow(Flow):
    """
    HTTP flow combining request and response.
    """
    id: str = field(default_factory=lambda: "http-flow")
    type: FlowType = FlowType.HTTP
    request: Optional[HTTPRequest] = None
    response: Optional[HTTPResponse] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        if self.request:
            return f"<HTTPFlow {self.request.method} {self.request.authority}{self.request.path}>"
        return f"<HTTPFlow {self.id}>"