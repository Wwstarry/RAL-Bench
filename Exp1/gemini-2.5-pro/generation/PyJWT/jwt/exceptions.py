class JWTError(Exception):
    """Base class for all exceptions in this library."""

    pass


class DecodeError(JWTError):
    """Raised when a token cannot be decoded because it's malformed."""

    pass


class ExpiredSignatureError(DecodeError):
    """Raised when a token's "exp" claim indicates it has expired."""

    pass


class InvalidSignatureError(DecodeError):
    """Raised when a token's signature doesn't match the one provided."""

    pass


class InvalidAlgorithmError(DecodeError):
    """Raised when the algorithm in the header is not in the allowed list."""

    pass


class InvalidTokenError(DecodeError):
    """A superclass for all token validation errors."""

    pass