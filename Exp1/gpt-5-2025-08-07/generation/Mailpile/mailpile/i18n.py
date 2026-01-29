"""
Minimal i18n passthrough helper.

This module provides gettext-like helpers, but defaults to identity
functions if gettext infrastructure is not available or not configured.
"""

try:
    import gettext as _gettext_mod
except Exception:  # pragma: no cover
    _gettext_mod = None


def _identity(text):
    return text


def _nidentity(singular, plural, n):
    return singular if int(n) == 1 else plural


# Resolve gettext functions if available, otherwise default to passthrough
if _gettext_mod is not None:
    # Use the global gettext API if available
    _ = getattr(_gettext_mod, "gettext", _identity)
    ngettext = getattr(_gettext_mod, "ngettext", _nidentity)
else:  # pragma: no cover
    _ = _identity
    ngettext = _nidentity


def N_(text):
    """
    Mark a translatable string without actually translating it.
    This is commonly used to mark strings for extraction.
    """
    return text


def gettext(text):
    """
    Compatibility alias for gettext, returns translated text or the original.
    """
    return _(text)


def n_gettext(singular, plural, n):
    """
    Compatibility alias which returns the correct pluralization according to n.
    """
    return ngettext(singular, plural, n)