"""Internationalization support for humanize."""

import gettext
import os

_TRANSLATIONS = None
_TRANSLATION_DOMAIN = "humanize"


class NullTranslations:
    """A mock translation class that returns the original string."""

    def gettext(self, message):
        return message

    def ngettext(self, singular, plural, n):
        return singular if n == 1 else plural


def gettext(message):
    """Gets a translation for a message."""
    return _TRANSLATIONS.gettext(message)


def ngettext(singular, plural, n):
    """Gets a pluralized translation for a message."""
    return _TRANSLATIONS.ngettext(singular, plural, n)


def activate(locale, path=None):
    """
    Activates a specific locale for translation.

    Looks for a message catalog in the standard locations, or in the
    given path.
    """
    global _TRANSLATIONS
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "locale")

    try:
        translation = gettext.translation(_TRANSLATION_DOMAIN, path, [locale])
        _TRANSLATIONS = translation
    except (IOError, OSError):
        _TRANSLATIONS = NullTranslations()


def deactivate():
    """Deactivates translation and returns to the default."""
    global _TRANSLATIONS
    _TRANSLATIONS = NullTranslations()


# Initialize with default (no translation)
deactivate()