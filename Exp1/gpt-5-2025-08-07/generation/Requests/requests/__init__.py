from . import api
from .sessions import Session
from .models import Request, PreparedRequest, Response
from .exceptions import (
    RequestException,
    HTTPError,
    Timeout,
    ConnectionError,
    TooManyRedirects,
    InvalidURL,
)
from .auth import HTTPBasicAuth

__all__ = [
    "request",
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "head",
    "options",
    "Session",
    "Request",
    "PreparedRequest",
    "Response",
    "RequestException",
    "HTTPError",
    "Timeout",
    "ConnectionError",
    "TooManyRedirects",
    "InvalidURL",
    "HTTPBasicAuth",
]

__version__ = "0.1.0"

# expose module-level helper functions
request = api.request
get = api.get
post = api.post
put = api.put
patch = api.patch
delete = api.delete
head = api.head
options = api.options