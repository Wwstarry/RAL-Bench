class PyJWTError(Exception):
    pass

class DecodeError(PyJWTError):
    pass

class ExpiredSignatureError(DecodeError):
    pass

class InvalidSignatureError(DecodeError):
    pass