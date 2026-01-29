class RequestException(Exception):
    """Base exception for all request-related errors."""
    def __init__(self, *args, request=None, response=None, **kwargs):
        super().__init__(*args)
        self.request = request
        self.response = response


class HTTPError(RequestException):
    """An HTTP error occurred."""


class ConnectionError(RequestException):
    """A network problem occurred."""


class Timeout(RequestException):
    """The request timed out."""


class TooManyRedirects(RequestException):
    """Exceeded the configured number of maximum redirects."""


class InvalidURL(RequestException):
    """The URL provided was invalid."""