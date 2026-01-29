from __future__ import annotations

from .sessions import Session


def request(method, url, **kwargs):
    with Session() as s:
        return s.request(method=method, url=url, **kwargs)


def get(url, params=None, **kwargs):
    kwargs.setdefault("allow_redirects", True)
    return request("GET", url, params=params, **kwargs)


def post(url, data=None, json=None, **kwargs):
    return request("POST", url, data=data, json=json, **kwargs)


def put(url, data=None, **kwargs):
    return request("PUT", url, data=data, **kwargs)


def delete(url, **kwargs):
    return request("DELETE", url, **kwargs)


def head(url, **kwargs):
    # requests default is allow_redirects=False for HEAD; acceptable.
    kwargs.setdefault("allow_redirects", False)
    return request("HEAD", url, **kwargs)


def options(url, **kwargs):
    kwargs.setdefault("allow_redirects", True)
    return request("OPTIONS", url, **kwargs)


def patch(url, data=None, **kwargs):
    return request("PATCH", url, data=data, **kwargs)