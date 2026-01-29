class PyJWTError(Exception):
    """Base class for all exceptions"""
    pass

class InvalidTokenError(PyJWTError):
    pass

class DecodeError(InvalidTokenError):
    pass

class InvalidSignatureError(DecodeError):
    pass

class ExpiredSignatureError(InvalidTokenError):
    pass