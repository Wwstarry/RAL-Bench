from .api_jwt import PyJWT
from .exceptions import (
    PyJWTError, InvalidTokenError, DecodeError,
    InvalidSignatureError, ExpiredSignatureError
)

_jwt_global = PyJWT()

def encode(payload, key, algorithm="HS256", **kwargs):
    return _jwt_global.encode(payload, key, algorithm, **kwargs)

def decode(token, key, algorithms=None, options=None, leeway=0, **kwargs):
    return _jwt_global.decode(token, key, algorithms=algorithms, options=options, leeway=leeway, **kwargs)