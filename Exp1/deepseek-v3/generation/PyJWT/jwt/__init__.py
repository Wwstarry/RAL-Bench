from .api_jwt import PyJWT
from .exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
)

jwt = PyJWT()

encode = jwt.encode
decode = jwt.decode

__all__ = [
    "encode",
    "decode",
    "DecodeError",
    "ExpiredSignatureError",
    "InvalidSignatureError",
]