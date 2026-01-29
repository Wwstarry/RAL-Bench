import gettext as _gettext
from typing import Optional


_translator = None


def gettext(msg: str) -> str:
    if msg is None:
        return ''
    if _translator is None:
        return str(msg)
    return _translator.gettext(str(msg))


def ngettext(singular: str, plural: str, n: int) -> str:
    if singular is None:
        singular = ''
    if plural is None:
        plural = ''
    if _translator is None:
        return str(singular) if n == 1 else str(plural)
    return _translator.ngettext(str(singular), str(plural), n)


def ActivateTranslation(language: Optional[str] = None,
                        localedir: Optional[str] = None,
                        domain: Optional[str] = None) -> None:
    """
    Attempt to activate gettext translations. Safe no-op if catalogs missing.
    """
    global _translator
    if domain is None:
        domain = 'mailpile'

    try:
        # fallback=False would raise if missing; we want safe no-op.
        trans = _gettext.translation(domain=domain,
                                     localedir=localedir,
                                     languages=([language] if language else None),
                                     fallback=True)
        _translator = trans
    except Exception:
        _translator = None