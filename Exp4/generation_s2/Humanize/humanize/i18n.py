"""
Minimal i18n stubs compatible with a subset of the reference humanize project.

The upstream project integrates with gettext and supports multiple locales.
For this kata we provide:
- activate(locale): set the active locale identifier
- deactivate(): clear locale (back to default)
- get_translation(): returns a translation function (identity)
- gettext alias '_': translation function

This is sufficient for code paths that call humanize.i18n.activate() or '_()'.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Optional

_ACTIVE_LOCALE: Optional[str] = None


def activate(locale: str) -> None:
    global _ACTIVE_LOCALE
    _ACTIVE_LOCALE = locale


def deactivate() -> None:
    global _ACTIVE_LOCALE
    _ACTIVE_LOCALE = None


def get_active() -> Optional[str]:
    return _ACTIVE_LOCALE


def get_translation() -> Callable[[str], str]:
    # No real translations shipped in this kata; identity is enough for tests
    return lambda s: s


def gettext(message: str) -> str:
    return message


_ = gettext


@contextmanager
def activated(locale: str):
    prev = _ACTIVE_LOCALE
    activate(locale)
    try:
        yield
    finally:
        global _ACTIVE_LOCALE
        _ACTIVE_LOCALE = prev