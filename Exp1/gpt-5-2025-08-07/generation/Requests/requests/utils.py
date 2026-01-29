from collections.abc import MutableMapping
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
import re


class CaseInsensitiveDict(MutableMapping):
    def __init__(self, data=None, **kwargs):
        self._store = {}
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, _ in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        return ((lowerkey, keyval[1]) for lowerkey, keyval in self._store.items())

    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __contains__(self, key):
        return key.lower() in self._store

    def items(self):
        return ((casedkey, value) for casedkey, value in self._store.values())

    def to_dict(self):
        return dict(self.items())


def merge_setting(request_setting, session_setting):
    if request_setting is None:
        return session_setting
    return request_setting


def merge_cookies(cookie_dict_a, cookie_dict_b):
    """Simple cookie merger: b overrides a on same keys."""
    merged = {}
    if cookie_dict_a:
        merged.update(cookie_dict_a)
    if cookie_dict_b:
        merged.update(cookie_dict_b)
    return merged


def add_params_to_url(url, params):
    if not params:
        return url
    if isinstance(params, (list, tuple)):
        query_pairs = list(params)
    elif isinstance(params, dict):
        query_pairs = list(params.items())
    else:
        # fallback: try iterable of pairs
        query_pairs = list(params)
    scheme, netloc, path, query, fragment = urlsplit(url)
    existing = parse_qsl(query, keep_blank_values=True)
    all_q = existing + query_pairs
    new_query = urlencode(all_q, doseq=True)
    return urlunsplit((scheme, netloc, path, new_query, fragment))


_charset_re = re.compile(r"charset=([\w-]+)", re.I)


def get_encoding_from_headers(headers):
    content_type = headers.get("Content-Type") or headers.get("content-type")
    if not content_type:
        return None
    m = _charset_re.search(content_type)
    if m:
        return m.group(1).strip("'\"")
    return None