"""
Exception hierarchy roughly compatible with `requests.exceptions`.
Only a subset required for the tests is provided.
"""


class RequestException(Exception):
    """Base exception for all requests errors."""


class HTTPError(RequestException):
    """An HTTP error (status >= 400)."""

    def __init__(self, message="", response=None):
        super().__init__(message)
        self.response = response


class ConnectionError(RequestException):
    """A network problem (e.g. DNS failure, refused connection, etc)."""


class Timeout(RequestException):
    """The request timed out."""


class TooManyRedirects(RequestException):
    """Exceeded configured number of maximum redirections."""