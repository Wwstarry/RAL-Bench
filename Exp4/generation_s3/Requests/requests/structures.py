from __future__ import annotations


class CaseInsensitiveDict(dict):
    """
    Minimal case-insensitive dict for HTTP headers.

    Stores original casing for keys as inserted last, but lookup is case-insensitive.
    """

    def __init__(self, data=None, **kwargs):
        super().__init__()
        self._store = {}  # lower_key -> (original_key, value)
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        lk = key.lower() if isinstance(key, str) else key
        self._store[lk] = (key, value)

    def __getitem__(self, key):
        lk = key.lower() if isinstance(key, str) else key
        return self._store[lk][1]

    def __delitem__(self, key):
        lk = key.lower() if isinstance(key, str) else key
        del self._store[lk]

    def __contains__(self, key):
        lk = key.lower() if isinstance(key, str) else key
        return lk in self._store

    def get(self, key, default=None):
        lk = key.lower() if isinstance(key, str) else key
        if lk in self._store:
            return self._store[lk][1]
        return default

    def items(self):
        for _, (ok, v) in self._store.items():
            yield ok, v

    def keys(self):
        for _, (ok, _) in self._store.items():
            yield ok

    def values(self):
        for _, (_, v) in self._store.items():
            yield v

    def update(self, data=None, **kwargs):
        if data is None:
            data = {}
        if hasattr(data, "items"):
            for k, v in data.items():
                self[k] = v
        else:
            for k, v in data:
                self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    def copy(self):
        return CaseInsensitiveDict(dict(self.items()))

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self._store)

    def __repr__(self):
        return f"{self.__class__.__name__}({dict(self.items())!r})"

    def to_dict(self):
        return dict(self.items())