"""
Internationalization support for humanize.
"""

_CURRENT_LOCALE = "en_US"


def activate(locale):
    """
    Activate a locale.
    
    Args:
        locale: Locale code to activate
    """
    global _CURRENT_LOCALE
    _CURRENT_LOCALE = locale


def deactivate():
    """
    Deactivate the current locale and return to default.
    """
    global _CURRENT_LOCALE
    _CURRENT_LOCALE = "en_US"


def get_current_locale():
    """
    Get the currently active locale.
    
    Returns:
        Current locale code
    """
    return _CURRENT_LOCALE