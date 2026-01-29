"""
Internationalization support for humanize.
"""
import gettext as _gettext
import os
from typing import Optional

__all__ = ["activate", "deactivate", "gettext", "ngettext"]

_DEFAULT_LOCALE_PATH = os.path.join(os.path.dirname(__file__), "locale")
_current_translation = None


def activate(locale: str, path: Optional[str] = None) -> None:
    """
    Activate internationalization for a specific locale.

    Args:
        locale: The locale name (e.g. 'en_US')
        path: The path to the locale directory. If None, the default location
              is used.
    """
    global _current_translation
    if path is None:
        path = _DEFAULT_LOCALE_PATH
    if locale:
        _current_translation = _gettext.translation(
            "humanize", path, [locale], fallback=True
        )


def deactivate() -> None:
    """Deactivate internationalization."""
    global _current_translation
    _current_translation = None


def gettext(message: str) -> str:
    """
    Translate a message.

    Args:
        message: The message to translate.
    
    Returns:
        The translated message or the original message if no translation exists.
    """
    global _current_translation
    if _current_translation is not None:
        if hasattr(_current_translation, "gettext"):
            return _current_translation.gettext(message)
    return message


def ngettext(singular: str, plural: str, n: int) -> str:
    """
    Translate a message with singular and plural forms.

    Args:
        singular: The singular form of the message.
        plural: The plural form of the message.
        n: The number used to determine which form to use.
    
    Returns:
        The translated message or the original message if no translation exists.
    """
    global _current_translation
    if _current_translation is not None:
        if hasattr(_current_translation, "ngettext"):
            return _current_translation.ngettext(singular, plural, n)
    if n == 1:
        return singular
    return plural