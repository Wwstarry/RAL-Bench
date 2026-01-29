from typing import Any, Dict, Optional

class Request:
    method: Optional[str]
    url: Optional[str]
    headers: Dict[str, Any]
    data: Any
    params: Any
    auth: Any
    cookies: Any
    json: Any
    def __init__(self, method: str | None = ..., url: str | None = ..., headers: Any = ..., files: Any = ..., data: Any = ..., params: Any = ..., auth: Any = ..., cookies: Any = ..., json: Any = ...) -> None: ...
    def prepare(self) -> PreparedRequest: ...

class PreparedRequest:
    method: str
    url: str
    headers: Dict[str, Any]
    body: Any
    def prepare(self, method: Any = ..., url: Any = ..., headers: Any = ..., files: Any = ..., data: Any = ..., params: Any = ..., auth: Any = ..., cookies: Any = ..., json: Any = ...) -> "PreparedRequest": ...

class Response:
    status_code: int
    headers: Dict[str, Any]
    url: str
    reason: str
    request: Any
    history: list
    encoding: Optional[str]
    @property
    def ok(self) -> bool: ...
    @property
    def content(self) -> bytes: ...
    @property
    def text(self) -> str: ...
    def json(self) -> Any: ...
    def raise_for_status(self) -> None: ...