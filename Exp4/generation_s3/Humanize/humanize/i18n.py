"""
Minimal i18n scaffolding.

The reference `humanize` package supports multiple locales. For this benchmark we
provide a tiny subset of that interface so other modules can call gettext-like
functions without requiring external catalogs.
"""

from __future__ import annotations

from typing import Optional

_LANGUAGE: Optional[str] = None


def activate(locale: str) -> None:
    global _LANGUAGE
    _LANGUAGE = str(locale) if locale is not None else None


def deactivate() -> None:
    global _LANGUAGE
    _LANGUAGE = None


def get_language() -> Optional[str]:
    return _LANGUAGE


def gettext(message: str) -> str:
    # English-only stub
    return message


def ngettext(singular: str, plural: str, n: int) -> str:
    return singular if int(n) == 1 else plural


def localize(number_string: str) -> str:
    # Locale-aware formatting is out of scope for this implementation.
    return number_string