class PyJWTError(Exception):
    """Base class for all exceptions"""

    pass


class InvalidTokenError(PyJWTError):
    """Raised when a token is invalid."""

    pass


class DecodeError(InvalidTokenError):
    """Raised when a token cannot be decoded because it's malformed."""

    pass


class ExpiredSignatureError(InvalidTokenError):
    """Raised when a token's expiration time has passed."""

    pass


class InvalidSignatureError(InvalidTokenError):
    """Raised when a signature is invalid."""

    pass