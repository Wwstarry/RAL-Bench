"""
Internationalization support for humanize.

This module provides basic i18n infrastructure. Currently supports English only.
"""

from typing import Dict, Optional

# Translation dictionary structure
_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {},
}

_CURRENT_LOCALE = "en"


def get_locale() -> str:
    """
    Get the current locale.
    
    Returns:
        Current locale code
    """
    return _CURRENT_LOCALE


def set_locale(locale: str) -> None:
    """
    Set the current locale.
    
    Args:
        locale: Locale code to set
    """
    global _CURRENT_LOCALE
    if locale not in _TRANSLATIONS:
        _TRANSLATIONS[locale] = {}
    _CURRENT_LOCALE = locale


def activate(locale: str) -> None:
    """
    Activate a locale.
    
    Args:
        locale: Locale code to activate
    """
    set_locale(locale)


def deactivate() -> None:
    """
    Deactivate the current locale and return to default.
    """
    global _CURRENT_LOCALE
    _CURRENT_LOCALE = "en"


def register(locale: str, translations: Dict[str, str]) -> None:
    """
    Register translations for a locale.
    
    Args:
        locale: Locale code
        translations: Dictionary of translations
    """
    if locale not in _TRANSLATIONS:
        _TRANSLATIONS[locale] = {}
    _TRANSLATIONS[locale].update(translations)


def translate(message: str, locale: Optional[str] = None) -> str:
    """
    Translate a message to the specified locale.
    
    Args:
        message: Message to translate
        locale: Locale code (uses current locale if not specified)
    
    Returns:
        Translated message or original if translation not found
    """
    if locale is None:
        locale = _CURRENT_LOCALE
    
    if locale in _TRANSLATIONS and message in _TRANSLATIONS[locale]:
        return _TRANSLATIONS[locale][message]
    
    return message