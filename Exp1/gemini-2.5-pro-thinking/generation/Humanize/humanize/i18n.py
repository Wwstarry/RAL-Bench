import gettext
import os
import threading

# Path to the locales directory
LOCALE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locale")

# Thread-local storage for translations
_TRANSLATIONS = threading.local()
_TRANSLATIONS.trans = gettext.NullTranslations()


def gettext(message):
    """Get the translation for a given message."""
    return _TRANSLATIONS.trans.gettext(message)


def ngettext(singular, plural, n):
    """Get the pluralized translation for a given message."""
    return _TRANSLATIONS.trans.ngettext(singular, plural, n)


def pgettext(context, message):
    """
    Get the translation for a message in a specific context.
    This is a fallback implementation.
    """
    # The standard gettext API does not support contexts.
    # A common convention is to use a separator.
    # The reference library uses `\x04`.
    context_message = f"{context}\x04{message}"
    translation = gettext(context_message)
    if translation == context_message:
        return message
    return translation


def activate(locale, path=None):
    """Activate a locale."""
    if path is None:
        path = LOCALE_PATH
    try:
        trans = gettext.translation("humanize", localedir=path, languages=[locale])
        _TRANSLATIONS.trans = trans
    except (IOError, OSError):
        _TRANSLATIONS.trans = gettext.NullTranslations()


def deactivate():
    """Deactivate the current locale and revert to the default."""
    _TRANSLATIONS.trans = gettext.NullTranslations()


# For convenience
_ = gettext