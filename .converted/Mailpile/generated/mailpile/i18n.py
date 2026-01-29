# -*- coding: utf-8 -*-
"""
gettext passthrough helper.

The original Mailpile supports runtime locale switching and integrates
with gettext catalogs. For this benchmark slice we provide a safe,
dependency-free subset that behaves like a passthrough (identity)
translator, with a minimal API compatible with common Mailpile usage.
"""




def gettext(msg: str) -> str:
    return msg


def ngettext(singular: str, plural: str, n: int) -> str:
    return singular if n == 1 else plural


# Common alias patterns used in Mailpile code.
_ = gettext