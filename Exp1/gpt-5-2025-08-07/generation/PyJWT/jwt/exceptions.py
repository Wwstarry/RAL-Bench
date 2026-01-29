class PyJWTError(Exception):
    """Base class for PyJWT errors."""


class InvalidTokenError(PyJWTError):
    """Base class for token-related errors."""


class DecodeError(InvalidTokenError):
    """Raised when a token cannot be decoded or verification parameters are invalid."""


class ExpiredSignatureError(InvalidTokenError):
    """Raised when a token's exp claim indicates it has expired."""


class InvalidSignatureError(InvalidTokenError):
    """Raised when the signature is invalid."""


class InvalidAlgorithmError(PyJWTError):
    """Raised when an algorithm is invalid or unsupported."""