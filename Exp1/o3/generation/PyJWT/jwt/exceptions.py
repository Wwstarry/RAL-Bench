"""
Exception classes used and exposed by the minimal jwt implementation.
"""

class PyJWTError(Exception):
    """Base-class for all custom exceptions raised by this jwt module."""
    pass


class InvalidTokenError(PyJWTError):
    """Generic error raised for problems with a JWT."""
    pass


class DecodeError(InvalidTokenError):
    """Raised when a token cannot be decoded."""
    pass


class InvalidSignatureError(InvalidTokenError):
    """Raised when a signature does not match the token contents."""
    pass


class ExpiredSignatureError(InvalidTokenError):
    """Raised when a token's 'exp' claim indicates it has expired."""
    pass