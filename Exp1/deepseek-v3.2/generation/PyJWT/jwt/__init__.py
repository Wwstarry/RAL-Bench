"""
Pure Python JSON Web Token (JWT) implementation
"""
from .api_jwt import encode, decode
from .exceptions import (
    ExpiredSignatureError,
    InvalidSignatureError,
    DecodeError,
)

__all__ = [
    'encode',
    'decode',
    'ExpiredSignatureError',
    'InvalidSignatureError',
    'DecodeError',
]

__version__ = '1.0.0'