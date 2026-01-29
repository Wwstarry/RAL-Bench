"""
Minimal i18n support layer.

The real humanize library integrates with gettext; here we provide a simple
no-op translation interface so that function signatures and calls can exist
without external dependencies.
"""

from contextlib import contextmanager
from typing import Optional

_current_locale: Optional[str] = None


def get_language():
    return _current_locale


def activate(locale: Optional[str]):
    global _current_locale
    _current_locale = locale


def deactivate():
    activate(None)


def gettext(message: str) -> str:
    # No-op translation
    return message


def ngettext(singular: str, plural: str, n: int) -> str:
    return singular if n == 1 else plural


@contextmanager
def override(locale: Optional[str]):
    """
    Context manager to temporarily override the active locale.
    """
    prev = get_language()
    try:
        activate(locale)
        yield
    finally:
        activate(prev)