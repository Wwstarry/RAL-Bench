"""
HTTP message types for mitmproxy.
"""

from typing import Optional, Dict, List, Any, Union
import dataclasses


@dataclasses.dataclass
class Headers:
    """HTTP headers container."""
    fields: List[tuple] = dataclasses.field(default_factory=list)
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get first header value for key (case-insensitive)."""
        key_lower = key.lower()
        for k, v in self.fields:
            if k.lower() == key_lower:
                return v
        return default
    
    def set_all(self, key: str, values: List[str]) -> None:
        """Set all values for a header, replacing existing ones."""
        self.fields = [(k, v) for k, v in self.fields if k.lower() != key.lower()]
        for v in values:
            self.fields.append((key, v))
    
    def keys(self) -> List[str]:
        """Return all header keys."""
        return [k for k, _ in self.fields]
    
    def items(self) -> List[tuple]:
        """Return all header fields."""
        return self.fields.copy()


@dataclasses.dataclass
class Request:
    """HTTP request."""
    method: str
    scheme: str
    host: str
    port: int
    path: str
    http_version: str = "HTTP/1.1"
    headers: Headers = dataclasses.field(default_factory=Headers)
    content: bytes = b""
    trailers: Optional[Headers] = None
    
    @property
    def pretty_host(self) -> str:
        """Return the host header or actual host."""
        host_header = self.headers.get("host")
        return host_header or self.host


@dataclasses.dataclass
class Response:
    """HTTP response."""
    http_version: str = "HTTP/1.1"
    status_code: int = 200
    reason: str = "OK"
    headers: Headers = dataclasses.field(default_factory=Headers)
    content: bytes = b""
    trailers: Optional[Headers] = None


@dataclasses.dataclass
class HTTPFlow:
    """A complete HTTP request/response pair."""
    request: Request
    response: Optional[Response] = None
    error: Optional[dict] = None
    
    @property
    def id(self) -> str:
        """Generate a unique ID for this flow."""
        import hashlib
        import time
        return hashlib.md5(f"{id(self)}{time.time()}".encode()).hexdigest()[:8]