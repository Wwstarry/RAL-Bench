"""
Minimal pure-Python JWT implementation compatible with core PyJWT APIs
used by the accompanying tests.
"""

from .api_jwt import encode, decode
from .exceptions import (
    PyJWTError,
    DecodeError,
    InvalidSignatureError,
    ExpiredSignatureError,
)

__all__ = [
    "encode",
    "decode",
    "PyJWTError",
    "DecodeError",
    "InvalidSignatureError",
    "ExpiredSignatureError",
]