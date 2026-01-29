class ExpiredSignatureError(Exception):
    """Raised when a token has expired."""
    pass

class InvalidSignatureError(Exception):
    """Raised when a token's signature is invalid."""
    pass

class DecodeError(Exception):
    """Raised when a token cannot be decoded."""
    pass