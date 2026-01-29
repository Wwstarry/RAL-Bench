import json
import base64
import hmac
import hashlib
import time
from typing import Any, Dict, List, Optional, Union

from .exceptions import (
    PyJWTError,
    ExpiredSignatureError,
    InvalidSignatureError,
    DecodeError,
)

__version__ = "1.0.0"
__all__ = ["encode", "decode", "PyJWTError", "ExpiredSignatureError", 
           "InvalidSignatureError", "DecodeError"]


def encode(
    payload: Dict[str, Any],
    key: str,
    algorithm: str = "HS256",
    **kwargs: Any
) -> str:
    """Encode a JWT token."""
    from .api_jwt import encode as _encode
    return _encode(payload, key, algorithm, **kwargs)


def decode(
    token: str,
    key: str,
    algorithms: List[str] = None,
    options: Optional[Dict[str, Any]] = None,
    leeway: int = 0,
    **kwargs: Any
) -> Dict[str, Any]:
    """Decode and verify a JWT token."""
    from .api_jwt import decode as _decode
    if algorithms is None:
        algorithms = ["HS256"]
    return _decode(token, key, algorithms, options, leeway, **kwargs)