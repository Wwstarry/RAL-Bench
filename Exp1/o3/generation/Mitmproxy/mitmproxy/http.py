"""
Highly reduced ‘http’ sub-module replicating only the public subset that
is exercised by the test-suite.

The real mitmproxy code distinguishes between requests and responses,
keeps a complete HTTP/1.x and HTTP/2 state-machine, provides content
viewers, caching, etc.  All of that is **far** outside the scope we need
here – so we only implement a paper-thin model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
from urllib.parse import urlparse

from .flow import Flow


@dataclass
class HTTPMessage:
    """
    Shared base class for HTTPRequest and HTTPResponse.
    """

    headers: Dict[str, str] = field(default_factory=dict)
    content: bytes = b""

    # ------------------------------------------------------------------
    # Utility helpers that exist on the real objects
    # ------------------------------------------------------------------
    def text(self, encoding: str = "utf-8") -> str:
        """Return the content decoded as *encoding*."""
        try:
            return self.content.decode(encoding)
        except Exception:
            # Keep things simple; never raise in the stub.
            return ""

    def __repr__(self) -> str:  # noqa: D401
        cname = self.__class__.__name__
        return f"<{cname} {len(self.content)} bytes>"


@dataclass
class HTTPRequest(HTTPMessage):
    """
    A minimal HTTP request representation.
    """

    method: str = "GET"
    url: str = "/"

    @property
    def host(self) -> str:
        """Return the host part extracted from :pyattr:`url`."""
        parsed = urlparse(self.url)
        return parsed.hostname or ""

    @property
    def path(self) -> str:
        parsed = urlparse(self.url)
        return parsed.path or "/"

    def __repr__(self) -> str:  # noqa: D401
        return f"<HTTPRequest {self.method} {self.url}>"


@dataclass
class HTTPResponse(HTTPMessage):
    """
    A minimal HTTP response representation.
    """

    status_code: int = 200
    reason: str = "OK"

    def __repr__(self) -> str:  # noqa: D401
        return f"<HTTPResponse {self.status_code} {self.reason}>"


@dataclass
class HTTPFlow(Flow):
    """
    A flow carrying exactly one HTTP request/response pair.
    """

    type: str = "http"
    request: HTTPRequest = field(default_factory=HTTPRequest)
    response: Optional[HTTPResponse] = None

    # The real mitmproxy adds many life-cycle hooks (intercept,
    # is_replay, etc.).  We don’t need them here – but exposing an easy
    # textual representation is handy when debugging the stub.
    def __repr__(self) -> str:  # noqa: D401
        req = f"{self.request.method} {self.request.url}"
        resp = f"{self.response.status_code}" if self.response else "–"
        return f"<HTTPFlow {req} -> {resp}>"