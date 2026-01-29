from .flow import Flow

class Request:
    def __init__(self):
        self.host = None
        self.port = None
        self.method = None
        self.scheme = None
        self.authority = None
        self.path = None
        self.http_version = None
        self.headers = None
        self.content = None
        self.trailers = None
        self.timestamp_start = None
        self.timestamp_end = None

class Response:
    def __init__(self):
        self.http_version = None
        self.status_code = None
        self.reason = None
        self.headers = None
        self.content = None
        self.trailers = None
        self.timestamp_start = None
        self.timestamp_end = None

class HTTPFlow(Flow):
    def __init__(self):
        super().__init__()
        self.request = Request()
        self.response = Response()