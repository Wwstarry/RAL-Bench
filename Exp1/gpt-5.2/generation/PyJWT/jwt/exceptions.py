class PyJWTError(Exception):
    """Base class for all JWT-related errors."""


class InvalidTokenError(PyJWTError):
    """Base class for token validation errors."""


class DecodeError(InvalidTokenError):
    """Raised when a token cannot be decoded or is otherwise invalid."""


class InvalidSignatureError(DecodeError):
    """Raised when signature verification fails."""


class ExpiredSignatureError(InvalidTokenError):
    """Raised when the token has expired (exp claim)."""