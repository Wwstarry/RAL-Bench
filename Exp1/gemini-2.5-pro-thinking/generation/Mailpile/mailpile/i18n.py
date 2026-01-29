# mailpile.i18n
#
# This is a simplified gettext passthrough helper for benchmarking.
# In a real application, this would integrate with the gettext module
# to provide translations.

import sys

# A mapping of locales to their translation objects.
# For this benchmark, we don't load any real translations.
_translations = {}
_current_language = 'en'


def set_language(language):
    """Sets the current language for translations."""
    global _current_language
    _current_language = language


def gettext(message):
    """
    Translates a message. This is a passthrough implementation.
    """
    # In a real implementation, this would look up the message
    # in the loaded translation catalog for the current language.
    return message


# The conventional alias for gettext
_ = gettext