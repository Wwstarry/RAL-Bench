class PyJWTError(Exception):
    """Base class for all JWT-related errors in this minimal PyJWT-compatible implementation."""


class DecodeError(PyJWTError):
    """Raised when a token cannot be decoded or is otherwise invalid."""


class InvalidSignatureError(DecodeError):
    """Raised when signature verification fails."""


class ExpiredSignatureError(DecodeError):
    """Raised when a token has expired (exp claim)."""