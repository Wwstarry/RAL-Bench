class DecodeError(Exception):
    pass

class InvalidSignatureError(DecodeError):
    pass

class ExpiredSignatureError(DecodeError):
    pass