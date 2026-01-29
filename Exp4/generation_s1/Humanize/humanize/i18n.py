from __future__ import annotations

from dataclasses import dataclass
import contextvars
from typing import Optional


@dataclass(frozen=True)
class Translation:
    locale: str = "en"

    def gettext(self, message: str) -> str:
        return message

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        return singular if n == 1 else plural


_translation_var: contextvars.ContextVar[Translation] = contextvars.ContextVar(
    "humanize_translation",
    default=Translation("en"),
)


def activate(locale: str) -> Translation:
    """
    Activate a locale. This lightweight implementation does not load catalogs;
    it only tracks locale and provides identity translations.
    """
    tr = Translation(locale or "en")
    _translation_var.set(tr)
    return tr


def deactivate() -> None:
    """Reset to default identity translation."""
    _translation_var.set(Translation("en"))


def get_translation() -> Translation:
    return _translation_var.get()


def gettext(message: str) -> str:
    return get_translation().gettext(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    return get_translation().ngettext(singular, plural, n)