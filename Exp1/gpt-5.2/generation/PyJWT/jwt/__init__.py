"""
Minimal, pure-Python JWT implementation compatible with core PyJWT APIs
as exercised by the bundled tests (HS256 only).
"""

from .api_jwt import encode, decode
from .exceptions import (
    PyJWTError,
    DecodeError,
    InvalidSignatureError,
    ExpiredSignatureError,
    InvalidTokenError,
)

__all__ = [
    "encode",
    "decode",
    "PyJWTError",
    "InvalidTokenError",
    "DecodeError",
    "InvalidSignatureError",
    "ExpiredSignatureError",
]