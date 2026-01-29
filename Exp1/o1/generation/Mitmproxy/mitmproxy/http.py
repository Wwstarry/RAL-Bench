"""
Minimal subset of mitmproxy.http for testing.
"""

class HTTPRequest:
    """
    Represents a minimal HTTP request object placeholder.
    """
    pass

class HTTPResponse:
    """
    Represents a minimal HTTP response object placeholder.
    """
    pass

class HTTPFlow:
    """
    Represents a minimal HTTP flow placeholder.
    """
    def __init__(self):
        self.request = HTTPRequest()
        self.response = HTTPResponse()