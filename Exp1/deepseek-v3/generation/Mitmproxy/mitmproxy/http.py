"""HTTP-related types and utilities"""

from typing import Optional, Dict, List, Any

class Headers:
    def __init__(self, fields: Optional[List[tuple]] = None):
        self.fields = fields or []
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        key_lower = key.lower()
        for k, v in self.fields:
            if k.lower() == key_lower:
                return v
        return default
    
    def keys(self) -> List[str]:
        return [k for k, _ in self.fields]
    
    def items(self) -> List[tuple]:
        return self.fields.copy()
    
    def __getitem__(self, key: str) -> str:
        result = self.get(key)
        if result is None:
            raise KeyError(key)
        return result

class Request:
    def __init__(self):
        self.host: Optional[str] = None
        self.port: int = 0
        self.method: str = "GET"
        self.scheme: str = "http"
        self.path: str = "/"
        self.http_version: str = "HTTP/1.1"
        self.headers = Headers()
        self.content: Optional[bytes] = None
        self.timestamp_start: float = 0.0
        self.timestamp_end: float = 0.0

class Response:
    def __init__(self):
        self.status_code: int = 200
        self.reason: str = "OK"
        self.http_version: str = "HTTP/1.1"
        self.headers = Headers()
        self.content: Optional[bytes] = None
        self.timestamp_start: float = 0.0
        self.timestamp_end: float = 0.0

class HTTPFlow:
    def __init__(self):
        self.id: str = ""
        self.request = Request()
        self.response: Optional[Response] = None
        self.error: Optional[dict] = None
        self.intercepted: bool = False
        self.modified: bool = False
        self.marked: bool = False
        self.comment: str = ""