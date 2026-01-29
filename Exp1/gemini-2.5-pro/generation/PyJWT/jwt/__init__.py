"""
JSON Web Token implementation

Minimum implementation based on PyJWT.
"""
from .api_jwt import encode, decode
from .exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
    JWTError,
)

__all__ = [
    "encode",
    "decode",
    "DecodeError",
    "ExpiredSignatureError",
    "InvalidSignatureError",
    "JWTError",
]