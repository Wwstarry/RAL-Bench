"""
JSON Web Token implementation compatible with PyJWT API.
"""

from jwt.api_jwt import PyJWT
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidTokenError,
)

_jwt_global_instance = PyJWT()

encode = _jwt_global_instance.encode
decode = _jwt_global_instance.decode

__all__ = [
    "encode",
    "decode",
    "DecodeError",
    "ExpiredSignatureError",
    "InvalidSignatureError",
    "InvalidTokenError",
]