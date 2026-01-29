class HTTPFlow:
    """
    Represents an HTTP flow, containing request and response objects.
    """
    def __init__(self, request=None, response=None):
        self.request = request
        self.response = response


class HTTPRequest:
    """
    Represents an HTTP request.
    """
    def __init__(self, method: str, url: str, headers: dict, body: bytes):
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body


class HTTPResponse:
    """
    Represents an HTTP response.
    """
    def __init__(self, status_code: int, headers: dict, body: bytes):
        self.status_code = status_code
        self.headers = headers
        self.body = body