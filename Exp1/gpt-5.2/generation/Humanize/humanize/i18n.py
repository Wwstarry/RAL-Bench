"""
Minimal i18n support.

The reference `humanize` library supports translation catalogs via gettext.
This pure-Python implementation provides a compatible surface for tests:
- activate/deactivate
- get_translation (returns an object with gettext/ngettext)
- gettext/ngettext wrappers

By default, English strings are returned.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class _NullTranslation:
    def gettext(self, message: str) -> str:
        return message

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        return singular if n == 1 else plural


_ACTIVE: Optional[_NullTranslation] = _NullTranslation()


def get_translation() -> _NullTranslation:
    return _ACTIVE or _NullTranslation()


def gettext(message: str) -> str:
    return get_translation().gettext(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    return get_translation().ngettext(singular, plural, n)


def activate(locale: str | None = None, path: str | None = None, domain: str = "humanize") -> None:
    # Pure-Python subset: no locale loading. Keep a translation object active.
    # Tests generally expect this function to exist and not fail.
    global _ACTIVE
    _ACTIVE = _NullTranslation()


def deactivate() -> None:
    global _ACTIVE
    _ACTIVE = _NullTranslation()