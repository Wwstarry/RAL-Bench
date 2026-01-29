"""
JWT exception types.
"""


class InvalidTokenError(Exception):
    """Base exception for all JWT errors."""
    pass


class DecodeError(InvalidTokenError):
    """Raised when a token cannot be decoded."""
    pass


class InvalidSignatureError(DecodeError):
    """Raised when signature verification fails."""
    pass


class ExpiredSignatureError(InvalidTokenError):
    """Raised when a token's exp claim indicates it has expired."""
    pass