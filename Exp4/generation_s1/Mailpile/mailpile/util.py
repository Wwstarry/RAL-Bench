import os
import random
import string
from typing import Any, Optional

from mailpile.i18n import gettext as _gettext

B36_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def safe_bytes(obj: Any, encoding: str = "utf-8", errors: str = "replace") -> bytes:
    if obj is None:
        return b""
    if isinstance(obj, bytes):
        return obj
    if isinstance(obj, bytearray):
        return bytes(obj)
    if isinstance(obj, str):
        return obj.encode(encoding, errors)
    return str(obj).encode(encoding, errors)


def safe_str(obj: Any, encoding: str = "utf-8", errors: str = "replace") -> str:
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, (bytes, bytearray)):
        return bytes(obj).decode(encoding, errors)
    return str(obj)


def try_decode(data: Any, encoding: str = "utf-8", errors: str = "replace") -> str:
    return safe_str(data, encoding=encoding, errors=errors)


def CleanText(text: Any, banned: Optional[str] = None, replace: str = " ") -> str:
    """
    Sanitize text by replacing ASCII control characters (except \t, \n, \r)
    with `replace`. If `banned` is provided, any character in that iterable
    is replaced as well.

    - None -> ''
    - bytes -> decoded as UTF-8 with replacement
    """
    s = safe_str(text)

    banned_set = set(banned) if banned else set()

    # Replace most C0 control chars except tab/newline/CR for safety.
    def _clean_char(ch: str) -> str:
        o = ord(ch)
        if ch in banned_set:
            return replace
        if o < 32 and ch not in ("\t", "\n", "\r"):
            return replace
        if o == 127:
            return replace
        return ch

    # Efficient join; no aggressive whitespace collapsing.
    return "".join(_clean_char(c) for c in s)


def b36(number: int) -> str:
    try:
        n = int(number)
    except Exception as e:
        raise ValueError("number must be an int") from e

    if n == 0:
        return "0"
    sign = ""
    if n < 0:
        sign = "-"
        n = -n

    digits = []
    while n:
        n, rem = divmod(n, 36)
        digits.append(B36_ALPHABET[rem])
    return sign + "".join(reversed(digits))


def unb36(text: Any) -> int:
    s = safe_str(text).strip()
    if s == "":
        raise ValueError("empty base36 value")

    sign = 1
    if s[0] == "-":
        sign = -1
        s = s[1:].strip()
    if s == "":
        raise ValueError("invalid base36 value")

    s = s.lower()
    allowed = set(B36_ALPHABET)
    for ch in s:
        if ch not in allowed:
            raise ValueError("invalid base36 character: %r" % ch)

    n = 0
    for ch in s:
        n = n * 36 + B36_ALPHABET.index(ch)
    return sign * n


_TRUE_STRINGS = {"1", "true", "t", "yes", "y", "on"}
_FALSE_STRINGS = {"0", "false", "f", "no", "n", "off", ""}


def truthy(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    s = safe_str(value).strip().lower()
    if s in _TRUE_STRINGS:
        return True
    if s in _FALSE_STRINGS:
        return False
    # Fall back: non-empty string is true
    return bool(s)


def boolify(value: Any) -> bool:
    return truthy(value)


def randomish_id(length: int = 8) -> str:
    try:
        length = int(length)
    except Exception:
        length = 8
    length = max(1, length)
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


# A tiny passthrough to mirror Mailpile patterns; may be used by callers.
_ = _gettext