"""
A tiny, self-contained subset of the 'requests' library API.

This implementation is intended for local testing against a local HTTP server.
It is NOT the third-party 'requests' package.
"""

from .api import request, get, post, put, delete, head, options, patch
from .sessions import Session
from .models import Request, Response
from .auth import HTTPBasicAuth
from . import exceptions

__all__ = [
    "request",
    "get",
    "post",
    "put",
    "delete",
    "head",
    "options",
    "patch",
    "Session",
    "Request",
    "Response",
    "HTTPBasicAuth",
    "exceptions",
]