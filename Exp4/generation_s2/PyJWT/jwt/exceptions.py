class PyJWTError(Exception):
    """Base class for all JWT-related errors."""


class DecodeError(PyJWTError):
    """Raised when a token cannot be decoded/parsed or is otherwise invalid."""


class InvalidSignatureError(DecodeError):
    """Raised when signature verification fails."""


class ExpiredSignatureError(DecodeError):
    """Raised when the 'exp' claim indicates the token has expired."""