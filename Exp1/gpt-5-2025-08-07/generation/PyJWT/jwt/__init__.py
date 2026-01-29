# Minimal pure-Python JWT implementation compatible with core PyJWT APIs

from .api_jwt import encode, decode
from .exceptions import (
    PyJWTError,
    InvalidTokenError,
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidAlgorithmError,
)

__all__ = [
    "encode",
    "decode",
    "PyJWTError",
    "InvalidTokenError",
    "DecodeError",
    "ExpiredSignatureError",
    "InvalidSignatureError",
    "InvalidAlgorithmError",
]

# Optional version indicator
__version__ = "0.1.0"