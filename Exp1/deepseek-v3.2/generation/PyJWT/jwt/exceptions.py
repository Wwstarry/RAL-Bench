"""
JWT Exceptions
"""

class PyJWTError(Exception):
    """Base exception for all PyJWT errors"""
    pass

class ExpiredSignatureError(PyJWTError):
    """Raised when a token's 'exp' claim indicates it has expired"""
    pass

class InvalidSignatureError(PyJWTError):
    """Raised when a token's signature doesn't match the payload"""
    pass

class DecodeError(PyJWTError):
    """Raised when a token cannot be decoded properly"""
    pass