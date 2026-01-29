"""
High level helper functions that proxy to a global Session.
"""

from typing import Any, Dict, Tuple, Union

from .sessions import Session

# Create a default global session similar to the real requests
_global_session = Session()

__all__ = [
    "request",
    "get",
    "post",
    "put",
    "delete",
    "head",
    "options",
    "patch",
    "session",
]


def request(method: str, url: str, **kwargs):
    """
    Construct and send a :class:`~requests.models.Response` object using
    the module-level *session*.
    """
    return _global_session.request(method, url, **kwargs)


def get(url: str, params: dict | None = None, **kwargs):
    return _global_session.get(url, params=params, **kwargs)


def post(url: str, data: Any = None, json: Any = None, **kwargs):
    return _global_session.post(url, data=data, json=json, **kwargs)


def put(url: str, data: Any = None, **kwargs):
    return _global_session.put(url, data=data, **kwargs)


def delete(url: str, **kwargs):
    return _global_session.delete(url, **kwargs)


def head(url: str, **kwargs):
    return _global_session.head(url, **kwargs)


def options(url: str, **kwargs):
    return _global_session.options(url, **kwargs)


def patch(url: str, data: Any = None, **kwargs):
    return _global_session.patch(url, data=data, **kwargs)


def session() -> Session:
    """
    Return a brand new Session object (different from the module-level one).
    """
    return Session()