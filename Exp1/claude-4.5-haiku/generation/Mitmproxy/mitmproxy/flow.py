"""
Base flow abstractions for mitmproxy.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class FlowType(Enum):
    """Enumeration of flow types."""
    HTTP = "http"
    WEBSOCKET = "websocket"
    TCP = "tcp"
    UDP = "udp"


@dataclass
class Flow:
    """
    Base class for all flow types.
    """
    id: str = field(default_factory=lambda: "flow")
    type: FlowType = FlowType.HTTP
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"<Flow {self.id}>"


@dataclass
class Request:
    """
    Base request abstraction.
    """
    method: str = "GET"
    scheme: str = "http"
    authority: str = "example.com"
    path: str = "/"
    http_version: str = "HTTP/1.1"
    headers: Dict[str, str] = field(default_factory=dict)
    content: bytes = b""
    
    def __repr__(self) -> str:
        return f"<Request {self.method} {self.authority}{self.path}>"


@dataclass
class Response:
    """
    Base response abstraction.
    """
    http_version: str = "HTTP/1.1"
    status_code: int = 200
    reason: str = "OK"
    headers: Dict[str, str] = field(default_factory=dict)
    content: bytes = b""
    
    def __repr__(self) -> str:
        return f"<Response {self.status_code} {self.reason}>"