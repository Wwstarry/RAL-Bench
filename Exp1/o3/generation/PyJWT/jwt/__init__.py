"""
Minimal pure-Python replacement for the core API of the PyJWT library.
Only HMAC-SHA256 (HS256) is implemented as this is sufficient for the
test-suite bundled with this repository.

Usage examples
--------------

    import jwt

    token = jwt.encode({"some": "payload"}, "secret")
    data = jwt.decode(token, "secret", algorithms=["HS256"])
"""

from .exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidTokenError,
)

from .api_jwt import PyJWT

__all__ = [
    "encode",
    "decode",
    "PyJWT",
    "DecodeError",
    "InvalidSignatureError",
    "ExpiredSignatureError",
    "InvalidTokenError",
]

# A module-level PyJWT instance for the functional interface.
_jwt = PyJWT()

encode = _jwt.encode
decode = _jwt.decode