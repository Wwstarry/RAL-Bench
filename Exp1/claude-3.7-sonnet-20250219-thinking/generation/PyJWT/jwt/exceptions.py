class PyJWTError(Exception):
    """Base exception for all JWT exceptions."""
    pass


class DecodeError(PyJWTError):
    """Error raised when decoding fails."""
    pass


class InvalidTokenError(PyJWTError):
    """Error raised when the token is invalid."""
    pass


class InvalidSignatureError(InvalidTokenError):
    """Error raised when the signature is invalid."""
    pass


class ExpiredSignatureError(InvalidTokenError):
    """Error raised when the signature has expired."""
    pass