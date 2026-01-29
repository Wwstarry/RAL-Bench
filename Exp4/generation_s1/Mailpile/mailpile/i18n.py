import gettext as _gettext
import os
from typing import Optional

_LANGUAGE: Optional[str] = None
_TRANSLATION = None


def set_language(lang: Optional[str] = None) -> None:
    """
    Activate a language for gettext lookups.

    This is intentionally conservative and will fall back to passthrough
    translation if no catalogs are available.
    """
    global _LANGUAGE, _TRANSLATION
    _LANGUAGE = lang
    _TRANSLATION = None

    if not lang:
        return

    # Try a very small, defensive gettext setup. If it fails, we remain
    # in passthrough mode (tests expect passthrough by default).
    try:
        localedir = os.environ.get("MAILPILE_LOCALEDIR")
        domain = os.environ.get("MAILPILE_TEXTDOMAIN", "mailpile")
        _TRANSLATION = _gettext.translation(domain, localedir=localedir, languages=[lang], fallback=True)
    except Exception:
        _TRANSLATION = None


def activate(lang: Optional[str] = None) -> None:
    set_language(lang)


def get_language() -> Optional[str]:
    return _LANGUAGE


def gettext(msg) -> str:
    if msg is None:
        msg = ""
    if not isinstance(msg, str):
        msg = str(msg)

    if _TRANSLATION is not None:
        try:
            return _TRANSLATION.gettext(msg)
        except Exception:
            return msg
    return msg


def ngettext(singular, plural, n: int) -> str:
    # Passthrough behavior; try translation if available.
    singular = "" if singular is None else (singular if isinstance(singular, str) else str(singular))
    plural = "" if plural is None else (plural if isinstance(plural, str) else str(plural))
    try:
        n_int = int(n)
    except Exception:
        n_int = 0

    if _TRANSLATION is not None:
        try:
            return _TRANSLATION.ngettext(singular, plural, n_int)
        except Exception:
            pass
    return singular if n_int == 1 else plural


# Common convention
_ = gettext