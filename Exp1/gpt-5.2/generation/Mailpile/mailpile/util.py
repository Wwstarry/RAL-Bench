# -*- coding: utf-8 -*-
"""
Utilities: CleanText, base36 conversion, helpers.

This is a self-contained subset intended for tests which validate
happy-path behavior.
"""

from __future__ import annotations

import base64
import binascii
import re
import string
from typing import Any, Dict, Iterable, Optional, Tuple, Union

# -----------------------------------------------------------------------------
# CleanText
# -----------------------------------------------------------------------------

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE_RE = re.compile(r"\s+", re.UNICODE)


def CleanText(
    text: Any,
    *,
    maxlen: Optional[int] = None,
    replace_whitespace: bool = True,
    remove_controls: bool = True,
) -> str:
    """
    Normalize text for safe display and predictable tests.

    - Coerces input to str (bytes decoded as UTF-8 with replacement)
    - Optionally removes ASCII control chars
    - Optionally collapses whitespace to single spaces
    - Optionally truncates to maxlen
    """
    if text is None:
        s = ""
    elif isinstance(text, bytes):
        s = text.decode("utf-8", "replace")
    else:
        s = str(text)

    if remove_controls:
        s = _CONTROL_RE.sub("", s)

    if replace_whitespace:
        s = _WHITESPACE_RE.sub(" ", s).strip()

    if maxlen is not None and maxlen >= 0:
        s = s[:maxlen]
    return s


# -----------------------------------------------------------------------------
# base36 helpers
# -----------------------------------------------------------------------------

_B36_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
_B36_MAP = {c: i for i, c in enumerate(_B36_ALPHABET)}


def b36(number: int) -> str:
    """Convert non-negative int to base36 lowercase string."""
    if number < 0:
        raise ValueError("b36() requires a non-negative integer")
    if number == 0:
        return "0"
    out = []
    n = number
    while n:
        n, r = divmod(n, 36)
        out.append(_B36_ALPHABET[r])
    return "".join(reversed(out))


def unb36(value: Union[str, bytes]) -> int:
    """Convert base36 string to int."""
    if isinstance(value, bytes):
        s = value.decode("ascii", "strict")
    else:
        s = str(value)
    s = s.strip().lower()
    if not s:
        raise ValueError("unb36() requires a non-empty string")
    n = 0
    for ch in s:
        if ch not in _B36_MAP:
            raise ValueError("Invalid base36 digit: %r" % ch)
        n = n * 36 + _B36_MAP[ch]
    return n


# -----------------------------------------------------------------------------
# Small helpers used in other slices/tests
# -----------------------------------------------------------------------------

def escape_html(text: Any) -> str:
    s = CleanText(text, replace_whitespace=False, remove_controls=True)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def try_decode(value: Any, encoding: str = "utf-8") -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode(encoding, "replace")
    return str(value)


def b64w_encode(raw: bytes) -> str:
    """URL-safe base64 without padding."""
    if not isinstance(raw, (bytes, bytearray)):
        raise TypeError("b64w_encode expects bytes")
    return base64.urlsafe_b64encode(bytes(raw)).decode("ascii").rstrip("=")


def b64w_decode(text: Union[str, bytes]) -> bytes:
    """Decode URL-safe base64 without requiring padding."""
    if isinstance(text, bytes):
        s = text.decode("ascii", "strict")
    else:
        s = str(text)
    s = s.strip()
    pad = "=" * ((4 - (len(s) % 4)) % 4)
    try:
        return base64.urlsafe_b64decode((s + pad).encode("ascii"))
    except (binascii.Error, ValueError) as e:
        raise ValueError("Invalid base64") from e


def dict_merge(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for d in dicts:
        if d:
            out.update(d)
    return out


def split_email(addr: str) -> Tuple[str, str]:
    """
    Very small helper: split local@domain.
    Returns ('', '') if not parseable.
    """
    s = CleanText(addr, replace_whitespace=True)
    if "@" not in s:
        return ("", "")
    local, domain = s.rsplit("@", 1)
    if not local or not domain:
        return ("", "")
    return (local, domain.lower())