"""
Minimal i18n stub that mirrors the public interface of *humanize.i18n*.
No real translation is performed – we just provide the functions so that
libraries expecting the module do not crash.
"""

from __future__ import annotations

import contextlib
from typing import Iterator, Optional

# Keep track of “current locale” purely for completeness
_locale: Optional[str] = None


def activate(locale: str) -> None:
    global _locale
    _locale = locale


def deactivate() -> None:
    global _locale
    _locale = None


def get_language() -> Optional[str]:
    return _locale


@contextlib.contextmanager
def override(locale: str) -> Iterator[None]:
    """
    Context-manager that temporarily sets the active locale.  Does not translate
    anything; state is only remembered for inspection via :pyfunc:`get_language`.
    """
    old = _locale
    try:
        activate(locale)
        yield
    finally:
        activate(old)  # type: ignore[arg-type]


# Simple identity translation – the real library would return a lazy proxy.
def gettext(message: str) -> str:  # noqa: D401
    return message


# For completeness
def ngettext(singular: str, plural: str, n: int) -> str:
    return singular if n == 1 else plural