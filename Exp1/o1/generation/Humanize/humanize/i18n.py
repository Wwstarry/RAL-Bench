"""
i18n.py

Minimal stubs for a basic i18n mechanism. This is a no-op approach to keep the
library self-contained.
"""

_current_locale = None

def activate(locale):
    """
    Activate a fake locale (no-op). Real libraries would switch a translation context.
    """
    global _current_locale
    _current_locale = locale

def deactivate():
    """
    Deactivate the current locale (no-op).
    """
    global _current_locale
    _current_locale = None

def gettext(string):
    """
    Return the string unchanged (no-op).
    """
    return string

def ngettext(singular, plural, number):
    """
    Naive singular/plural no-op.
    """
    if number == 1:
        return singular
    return plural