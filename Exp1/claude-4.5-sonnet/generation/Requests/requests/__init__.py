"""
Requests HTTP Library
~~~~~~~~~~~~~~~~~~~~~

Requests is an elegant and simple HTTP library for Python, built for human beings.

Usage:

   >>> import requests
   >>> r = requests.get('https://www.python.org')
   >>> r.status_code
   200
"""

__version__ = '2.31.0'
__title__ = 'requests'
__description__ = 'Python HTTP for Humans.'
__url__ = 'https://requests.readthedocs.io'

from . import exceptions
from .api import request, get, head, post, patch, put, delete, options
from .models import Request, Response, PreparedRequest
from .sessions import Session, session
from .status_codes import codes
from .exceptions import (
    RequestException, Timeout, URLRequired,
    TooManyRedirects, HTTPError, ConnectionError,
    FileModeWarning, ConnectTimeout, ReadTimeout,
    JSONDecodeError, InvalidJSONError, ChunkedEncodingError,
    ContentDecodingError, StreamConsumedError,
    RetryError, UnrewindableBodyError,
    RequestsWarning, InvalidURL, InvalidHeader,
    InvalidProxyURL, ChunkedEncodingError,
    MissingSchema, InvalidSchema,
)

__all__ = [
    'request', 'get', 'head', 'post', 'patch', 'put', 'delete', 'options',
    'Request', 'Response', 'PreparedRequest',
    'Session', 'session',
    'codes',
    'RequestException', 'Timeout', 'URLRequired',
    'TooManyRedirects', 'HTTPError', 'ConnectionError',
    'FileModeWarning', 'ConnectTimeout', 'ReadTimeout',
    'JSONDecodeError', 'InvalidJSONError',
    'RequestsWarning', 'InvalidURL', 'InvalidHeader',
    'InvalidProxyURL', 'ChunkedEncodingError',
    'ContentDecodingError', 'StreamConsumedError',
    'RetryError', 'UnrewindableBodyError',
    'MissingSchema', 'InvalidSchema',
]