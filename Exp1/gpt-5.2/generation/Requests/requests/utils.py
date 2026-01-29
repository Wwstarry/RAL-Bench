import json as _json
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl


def super_len(obj):
    try:
        return len(obj)
    except Exception:
        return None


def to_native_string(s, encoding="utf-8"):
    if s is None:
        return None
    if isinstance(s, str):
        return s
    if isinstance(s, bytes):
        return s.decode(encoding, errors="replace")
    return str(s)


def json_dumps(data):
    return _json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def requote_uri(uri):
    return uri


def set_query_parameter(url, params):
    if not params:
        return url
    parts = list(urlsplit(url))
    query = dict(parse_qsl(parts[3], keep_blank_values=True))
    query.update(params)
    parts[3] = urlencode(query, doseq=True)
    return urlunsplit(parts)