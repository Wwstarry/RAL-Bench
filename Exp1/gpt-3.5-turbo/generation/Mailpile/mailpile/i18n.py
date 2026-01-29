def gettext(text):
    """
    Passthrough gettext helper for i18n.
    """
    return text


def ngettext(singular, plural, n):
    """
    Passthrough ngettext helper for i18n.
    """
    return singular if n == 1 else plural