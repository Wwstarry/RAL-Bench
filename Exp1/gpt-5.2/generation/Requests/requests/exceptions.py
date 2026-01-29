class RequestException(Exception):
    """Base exception for all request-related errors."""


class InvalidURL(RequestException):
    pass


class MissingSchema(InvalidURL):
    pass


class InvalidSchema(InvalidURL):
    pass


class URLRequired(InvalidURL):
    pass


class ConnectionError(RequestException):
    pass


class ProxyError(ConnectionError):
    pass


class SSLError(ConnectionError):
    pass


class Timeout(RequestException):
    pass


class TooManyRedirects(RequestException):
    pass


class HTTPError(RequestException):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


class ChunkedEncodingError(RequestException):
    pass


class ContentDecodingError(RequestException):
    pass


class StreamConsumedError(RequestException):
    pass