class PyJWTError(Exception):
    """Base class for all PyJWT errors."""
    pass


class ExpiredSignatureError(PyJWTError):
    """Raised when a token's signature has expired."""
    pass


class InvalidSignatureError(PyJWTError):
    """Raised when a token's signature is invalid."""
    pass


class DecodeError(PyJWTError):
    """Raised when a token cannot be decoded."""
    pass