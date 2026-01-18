"""
Tiny gettext passthrough used by tests.

Mailpile's full codebase has richer i18n; for this slice we only provide:
  - gettext: identity
  - ngettext: plural passthrough
  - _ and N_ aliases
"""


def gettext(msg: str) -> str:
    return msg


def ngettext(singular: str, plural: str, n: int) -> str:
    return singular if n == 1 else plural


_ = gettext


def N_(msg: str) -> str:
    # Marker for strings to be translated; runtime no-op.
    return msg