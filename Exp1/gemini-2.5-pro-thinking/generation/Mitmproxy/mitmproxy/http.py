from mitmproxy import flow

class Headers:
    """
    A minimal, safe-to-evaluate placeholder for HTTP headers.
    Behaves like a case-insensitive multi-dict.
    """
    def __init__(self, fields=None):
        self._fields = fields or []

    def __getitem__(self, key):
        key = key.lower()
        for k, v in self._fields:
            if k.lower() == key:
                return v
        raise KeyError(key)

    def __setitem__(self, key, value):
        self._fields.append((key, value))

    def __delitem__(self, key):
        key = key.lower()
        self._fields = [(k, v) for k, v in self._fields if k.lower() != key]

    def __iter__(self):
        return iter(self._fields)

    def keys(self):
        return [k for k, v in self._fields]

    def values(self):
        return [v for k, v in self._fields]

    def items(self):
        return self._fields

    def __len__(self):
        return len(self._fields)

class Request:
    """A minimal, safe-to-evaluate placeholder for an HTTP request."""
    def __init__(self, host, port, method, scheme, path, http_version, headers, content):
        self.host = host
        self.port = port
        self.method = method
        self.scheme = scheme
        self.path = path
        self.http_version = http_version
        self.headers = headers or Headers()
        self.content = content

class Response:
    """A minimal, safe-to-evaluate placeholder for an HTTP response."""
    def __init__(self, http_version, status_code, reason, headers, content):
        self.http_version = http_version
        self.status_code = status_code
        self.reason = reason
        self.headers = headers or Headers()
        self.content = content

class HTTPFlow(flow.Flow):
    """
    A minimal, safe-to-evaluate placeholder for an HTTPFlow.
    Contains a single HTTP transaction.
    """
    def __init__(self):
        super().__init__()
        self.request = None
        self.response = None
        self.error = None