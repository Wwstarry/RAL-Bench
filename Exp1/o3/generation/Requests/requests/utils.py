import io
import re
import json
from typing import Dict, Tuple, Union, Optional
from urllib.parse import quote, urlencode

__all__ = [
    "dict_from_cookiejar",
    "cookiejar_from_dict",
    "parse_header_links",
    "guess_json_utf",
    "get_encoding_from_headers",
    "urlencode_params",
]


def dict_from_cookiejar(cj) -> Dict[str, str]:
    """
    Convert a ``http.cookiejar.CookieJar`` into a plain ``dict``.
    """
    return {cookie.name: cookie.value for cookie in cj}


def cookiejar_from_dict(data: Dict[str, str]):
    """
    Convert a simple ``dict`` into a CookieJar instance.
    """
    import http.cookiejar

    jar = http.cookiejar.CookieJar()
    for name, value in data.items():
        cookie = http.cookiejar.Cookie(
            version=0,
            name=name,
            value=value,
            port=None,
            port_specified=False,
            domain="",
            domain_specified=False,
            domain_initial_dot=False,
            path="/",
            path_specified=True,
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={},
            rfc2109=False,
        )
        jar.set_cookie(cookie)
    return jar


# The helpers below are *very* small subsets of the real ones used by requests.


def parse_header_links(value: str):
    """
    Very naive Link header parser.
    """
    links = []
    for part in value.split(","):
        url_part, *rest = part.split(";")
        url_part = url_part.strip(" <>")
        info = {"url": url_part}
        for item in rest:
            if "=" in item:
                k, v = item.strip().split("=", 1)
                info[k.strip()] = v.strip('"')
        links.append(info)
    return links


def guess_json_utf(data: bytes) -> Optional[str]:
    """
    Return the probable JSON encoding given raw ``data``.
    """
    if not data:
        return None
    sample = data[:4]
    if sample.startswith(b"\xff\xfe") or sample.startswith(b"\xfe\xff"):
        return "utf-16"
    if sample.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    return "utf-8"


_CONTENT_TYPE_RE = re.compile(r"charset=([^\s;]+)", re.I)


def get_encoding_from_headers(headers) -> Optional[str]:
    """
    Extract the declared charset from ``Content-Type`` header if any.
    """
    content_type = headers.get("Content-Type", "")
    match = _CONTENT_TYPE_RE.search(content_type)
    if match:
        return match.group(1).strip("'\"")
    return None


def urlencode_params(params):
    """
    Encode *params* (dict or sequence) to a query string.
    """
    if params is None:
        return ""
    if isinstance(params, str):
        return quote(params, safe="")
    return urlencode(params, doseq=True)