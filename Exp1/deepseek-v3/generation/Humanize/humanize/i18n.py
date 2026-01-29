# Internationalization support - placeholder for actual implementation
# This would normally contain gettext integration and locale handling

def activate(locale=None):
    """Activate internationalization support for the specified locale."""
    pass

def deactivate():
    """Deactivate internationalization support."""
    pass

def gettext(message):
    """Return the localized translation of message."""
    return message

_ = gettext