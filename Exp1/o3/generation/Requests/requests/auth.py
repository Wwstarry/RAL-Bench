"""
Authentication helpers – only basic auth is implemented.
"""
import base64


class AuthBase:
    """Base class for authentication handlers."""

    def __call__(self, request):
        raise NotImplementedError("Auth handlers must implement __call__")


class HTTPBasicAuth(AuthBase):
    """
    Attaches HTTP Basic Authentication to the given Request object.
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __call__(self, request):
        user_pass = f"{self.username}:{self.password}".encode()
        b64 = base64.b64encode(user_pass).decode()
        request.headers["Authorization"] = f"Basic {b64}"
        return request