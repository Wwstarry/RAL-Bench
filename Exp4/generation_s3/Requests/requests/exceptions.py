class RequestException(Exception):
    """Base exception for all request-related errors."""


class InvalidURL(RequestException):
    pass


class MissingSchema(InvalidURL):
    pass


class InvalidSchema(InvalidURL):
    pass


class URLRequired(RequestException):
    pass


class ConnectionError(RequestException):
    pass


class Timeout(RequestException):
    pass


class TooManyRedirects(RequestException):
    pass


class HTTPError(RequestException):
    pass


class JSONDecodeError(ValueError):
    pass