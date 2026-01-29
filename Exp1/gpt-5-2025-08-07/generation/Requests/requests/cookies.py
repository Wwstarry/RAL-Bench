from collections.abc import MutableMapping


class RequestsCookieJar(MutableMapping):
    """
    A very small cookie jar that behaves like a dict of name -> value.
    This does not implement domain/path scoping. It is intentionally simple.
    """
    def __init__(self):
        self._cookies = {}

    def set(self, name, value):
        self._cookies[name] = value

    def get(self, name, default=None):
        return self._cookies.get(name, default)

    def get_dict(self):
        return dict(self._cookies)

    def update(self, other=None, **kwargs):
        if other is None:
            other = {}
        if hasattr(other, "items"):
            for k, v in other.items():
                self._cookies[k] = v
        else:
            for k, v in other:
                self._cookies[k] = v
        for k, v in kwargs.items():
            self._cookies[k] = v

    def __getitem__(self, key):
        return self._cookies[key]

    def __setitem__(self, key, value):
        self._cookies[key] = value

    def __delitem__(self, key):
        del self._cookies[key]

    def __iter__(self):
        return iter(self._cookies)

    def __len__(self):
        return len(self._cookies)

    def items(self):
        return self._cookies.items()