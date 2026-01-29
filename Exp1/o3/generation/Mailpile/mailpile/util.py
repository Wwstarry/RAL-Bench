"""
mailpile.util
=============

This module provides a handful of helpers that are frequently used
throughout the Mailpile code-base.  Only a very small subset is
implemented here – just enough for the unit-tests shipped with the kata.

Implemented bits
----------------
CleanText            – Minimal sanitiser for untrusted strings.
b36encode / decode   – Base-36 number/ASCII conversion.
safestr              – Best-effort conversion of arbitrary objects to str.
"""
from __future__ import unicode_literals, absolute_import

import string
import sys
from typing import Any

from mailpile.i18n import _

__all__ = [
    "CleanText",
    "b36encode",
    "b36decode",
    "safestr",
]


def safestr(value: Any, encoding: str = "utf-8", errors: str = "replace") -> str:
    """
    Convert *value* to :class:`str`, attempting to decode bytes using the
    supplied *encoding*.  Objects whose ``__str__`` raises exceptions are
    handled gracefully.

    This is **not** a faithful reproduction of Mailpile's implementation
    – it is merely good enough for the benchmark tests.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode(encoding, errors=errors)
    try:
        return str(value)
    except Exception:  # pragma: no cover
        # Last resort – represent the object by its type and id so we
        # never crash while logging or displaying debugging info.
        return "<%s 0x%x (unprintable)>" % (type(value).__name__, id(value))


class CleanText(str):
    """
    A **very** simplified version of the real ``mailpile.util.CleanText``.
    The goal is to strip / replace control characters and optionally
    collapse whitespace so malicious content cannot escape to the UI.

    Parameters
    ----------
    text:
        The text to clean.
    clean:
        Select a cleaning policy (only ``"printable"`` is recognised).
    replace:
        Character used as replacement for disallowed characters.
    collapse:
        Whether to collapse runs of whitespace into a single space.
    strip:
        Whether to strip leading / trailing whitespace.
    """

    PRINTABLE = set(bytes(string.printable, "ascii").decode("ascii"))

    def __new__(cls,
                text: Any,
                clean: str = "printable",
                replace: str = "?",
                collapse: bool = True,
                strip: bool = True):
        raw_text = safestr(text)

        # Prepare the whitelist.
        if clean == "printable":
            allowed = cls.PRINTABLE
        else:  # pragma: no cover
            raise ValueError(_("Unknown CleanText policy: %s") % clean)

        # Replace characters outside the whitelist.
        out_chars = []
        for ch in raw_text:
            if ch in allowed:
                out_chars.append(ch)
            else:
                out_chars.append(replace)
        cleaned = "".join(out_chars)

        # Collapse whitespace?
        if collapse:
            cleaned = " ".join(cleaned.split())

        # Strip?
        if strip:
            cleaned = cleaned.strip()

        # Return as an instance of this class.
        return super(CleanText, cls).__new__(cls, cleaned)


# --- Base-36 helpers ------------------------------------------------------- #
B36_ALPHABET = string.digits + string.ascii_lowercase


def b36encode(number: int) -> str:
    """
    Convert positive integer *number* to a lowercase base-36 string.

    >>> b36encode(35)
    'z'
    >>> b36encode(36)
    '10'
    """
    if not isinstance(number, int) or number < 0:
        raise ValueError("Only non-negative integers can be base36-encoded")

    if number == 0:
        return "0"

    digits = []
    while number:
        number, rem = divmod(number, 36)
        digits.append(B36_ALPHABET[rem])
    return "".join(reversed(digits))


def b36decode(text: str) -> int:
    """
    Parse a base-36 *text* string back into an integer.

    >>> b36decode('z')
    35
    >>> b36decode('10')
    36
    """
    if not text:
        raise ValueError("Empty string")
    text = text.lower()
    value = 0
    for ch in text:
        if ch not in B36_ALPHABET:
            raise ValueError("Invalid base36 digit: %r" % ch)
        value = value * 36 + B36_ALPHABET.index(ch)
    return value