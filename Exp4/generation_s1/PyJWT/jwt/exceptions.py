class PyJWTError(Exception):
    """Base class for all JWT-related errors."""


class DecodeError(PyJWTError):
    """Raised when a token cannot be decoded or validated."""


class InvalidSignatureError(DecodeError):
    """Raised when signature verification fails."""


class ExpiredSignatureError(DecodeError):
    """Raised when a token has expired (exp claim)."""