from __future__ import annotations

from typing import Optional

_current_app: Optional[object] = None


def _set_current_app(app) -> None:
    global _current_app
    _current_app = app


class _Proxy:
    def __init__(self, getter):
        self._getter = getter

    def __getattr__(self, name):
        return getattr(self._getter(), name)

    def __repr__(self) -> str:
        return repr(self._getter())


def _get_current_app():
    if _current_app is None:
        # Late import to avoid circular imports.
        from .app.base import _get_default_app
        return _get_default_app()
    return _current_app


current_app = _Proxy(_get_current_app)