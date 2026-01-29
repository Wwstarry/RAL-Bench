class JWTError(Exception):
    """Base exception for all JWT errors."""
    pass


class DecodeError(JWTError):
    """Exception raised when a JWT cannot be decoded."""
    pass


class InvalidSignatureError(DecodeError):
    """Exception raised when a JWT signature is invalid."""
    pass


class ExpiredSignatureError(DecodeError):
    """Exception raised when a JWT has expired."""
    pass


class InvalidKeyError(JWTError):
    """Exception raised when an invalid key is provided."""
    pass


class InvalidAlgorithmError(JWTError):
    """Exception raised when an invalid algorithm is specified."""
    pass