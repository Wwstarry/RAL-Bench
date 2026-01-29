from .api_jwt import PyJWT
from .exceptions import DecodeError, ExpiredSignatureError, InvalidSignatureError

__all__ = [
    "encode",
    "decode",
    "PyJWT",
    "DecodeError",
    "InvalidSignatureError",
    "ExpiredSignatureError",
]

_default_jwt = PyJWT()


def encode(payload, key, algorithm="HS256", **kwargs) -> str:
    return _default_jwt.encode(payload, key, algorithm=algorithm, **kwargs)


def decode(token, key, algorithms=["HS256"], options=None, leeway=0, **kwargs):
    return _default_jwt.decode(token, key=key, algorithms=algorithms, options=options, leeway=leeway, **kwargs)