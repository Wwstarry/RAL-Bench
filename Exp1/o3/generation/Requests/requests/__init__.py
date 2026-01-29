"""
A **very** small subset of the famous ``requests`` package API.

The goal of this re-implementation is *not* feature parity with the real
`requests` library – that would be far beyond the scope of the current
project – but rather to expose the handful of classes, functions and
attributes that the public tests need in order to execute successfully.

Only HTTP/HTTPS traffic to localhost (or any other reachable host) is
supported.  All network operations are implemented on top of the Python
standard library (`urllib.request` and friends) so that no additional
third-party dependency is required.
"""

from .api import delete, get, head, options, patch, post, put, request
from .sessions import Session
from .auth import HTTPBasicAuth
from .exceptions import (
    RequestException,
    HTTPError,
    ConnectionError,
    Timeout,
    TooManyRedirects,
)

__all__ = [
    "Session",
    "get",
    "post",
    "put",
    "delete",
    "head",
    "options",
    "patch",
    "request",
    "HTTPBasicAuth",
    "RequestException",
    "HTTPError",
    "ConnectionError",
    "Timeout",
    "TooManyRedirects",
]

__version__ = "0.1.0"