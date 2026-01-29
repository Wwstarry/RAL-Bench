class PyJWTError(Exception):
    """Base class for all PyJWT exceptions."""


class ExpiredSignatureError(PyJWTError):
    """Raised when a token's exp claim indicates it has expired."""


class InvalidSignatureError(PyJWTError):
    """Raised when signature verification fails."""


class DecodeError(PyJWTError):
    """Raised when decoding a token fails due to invalid format or data."""