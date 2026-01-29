class PyJWTError(Exception):
    """Base exception for all PyJWT errors"""

class ExpiredSignatureError(PyJWTError):
    """Raised when a token's exp claim indicates it has expired"""

class InvalidSignatureError(PyJWTError):
    """Raised when a token's signature is invalid"""

class DecodeError(PyJWTError):
    """Raised when a token cannot be decoded properly"""

__all__ = [
    "PyJWTError",
    "ExpiredSignatureError", 
    "InvalidSignatureError",
    "DecodeError",
]