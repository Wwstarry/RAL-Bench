"""
Utility helpers for text cleaning and base36 conversion.
"""

import os
import random
import string
import unicodedata


class CleanText:
    """
    CleanText removes or normalizes undesirable characters from text.

    Features:
    - Accepts str or bytes; bytes are decoded as UTF-8 with errors='replace'.
    - Removes control characters by default (ASCII < 32), except tabs/newlines.
    - Optionally strips, lowers, enforces a maximum length.
    - "banned" characters can be removed explicitly.
    - "allow" can whitelist allowed characters, removing everything else.

    Usage:
        CleanText(" Hello\tWorld!\n").text  -> "Hello\tWorld!\n"
        str(CleanText(b"\xffbad"))          -> "�bad" (decoded with replace)
        CleanText("FoO", lower=True).text   -> "foo"
    """

    DEFAULT_KEEP = {"\t", "\n"}

    def __init__(self, text,
                 banned=None,
                 allow=None,
                 encoding="utf-8",
                 strip=True,
                 lower=False,
                 maxlen=None):
        self.original = text
        self.encoding = encoding
        self._text = self._coerce(text, encoding=encoding)
        self._text = self._clean(self._text, banned=banned, allow=allow)
        if strip:
            self._text = self._text.strip()
        if lower:
            self._text = self._text.lower()
        if maxlen is not None and maxlen >= 0:
            self._text = self._text[:maxlen]

    @staticmethod
    def _coerce(text, encoding="utf-8"):
        if isinstance(text, bytes):
            return text.decode(encoding or "utf-8", errors="replace")
        elif text is None:
            return ""
        else:
            return str(text)

    @classmethod
    def _clean(cls, text, banned=None, allow=None):
        if allow is not None:
            allowed_set = set(allow)
            return "".join(ch for ch in text if ch in allowed_set)

        # Remove control characters except tab/newline
        cleaned = []
        banned_set = set(banned or "")
        for ch in text:
            if ch in banned_set:
                continue
            # Skip Cc category (control) except tab/newline
            if unicodedata.category(ch) == "Cc" and ch not in cls.DEFAULT_KEEP:
                continue
            cleaned.append(ch)
        return "".join(cleaned)

    @property
    def text(self):
        return self._text

    def __str__(self):
        return self._text

    def __repr__(self):
        return f"CleanText({self._text!r})"

    def as_string(self):
        return self._text

    def __len__(self):
        return len(self._text)


def safe_str(value, encoding="utf-8"):
    """
    Robust conversion of arbitrary values to a safe str.
    """
    return CleanText(value, encoding=encoding).text


_B36_ALPHABET = string.digits + string.ascii_lowercase
_B36_LOOKUP = {ch: i for i, ch in enumerate(_B36_ALPHABET)}


def b36(n):
    """
    Convert a non-negative integer to a base36 string.
    b36(0) -> "0"; b36(35) -> "z"; b36(36) -> "10"
    """
    if not isinstance(n, int):
        raise TypeError("b36 expects int")
    if n < 0:
        raise ValueError("b36 expects non-negative int")
    if n == 0:
        return "0"
    out = []
    while n > 0:
        n, r = divmod(n, 36)
        out.append(_B36_ALPHABET[r])
    return "".join(reversed(out))


def unb36(s):
    """
    Convert a base36 string to a non-negative integer. Case-insensitive.
    """
    if s is None:
        raise TypeError("unb36 expects string")
    s = str(s).strip().lower()
    if not s:
        raise ValueError("unb36 expects non-empty string")
    n = 0
    for ch in s:
        if ch not in _B36_LOOKUP:
            raise ValueError(f"Invalid base36 digit: {ch!r}")
        n = (n * 36) + _B36_LOOKUP[ch]
    return n


def secure_random_hex(nbytes=16):
    """
    Generate a cryptographically secure random hex string.
    """
    return os.urandom(int(nbytes)).hex()


def shorten(text, maxlen=80, ellipsis="…"):
    """
    Shorten text to at most maxlen characters, appending an ellipsis if needed.
    """
    t = safe_str(text)
    if len(t) <= maxlen:
        return t
    if maxlen <= len(ellipsis):
        return ellipsis[:maxlen]
    return t[:maxlen - len(ellipsis)] + ellipsis


def merge_dicts(base, override):
    """
    Shallow merge of two dicts, returning a new dict. Values from override take precedence.
    """
    result = dict(base or {})
    result.update(dict(override or {}))
    return result


def is_ascii(s):
    """
    Check whether a string contains only ASCII characters.
    """
    try:
        s.encode("ascii")
        return True
    except Exception:
        return False


def normalize_whitespace(s):
    """
    Normalize whitespace in a string: collapse consecutive spaces and trim.
    Tabs and newlines are converted to single spaces.
    """
    t = safe_str(s)
    t = t.replace("\t", " ").replace("\r", " ").replace("\n", " ")
    # Collapse multiple spaces
    out = []
    last_space = False
    for ch in t.strip():
        if ch == " ":
            if not last_space:
                out.append(ch)
            last_space = True
        else:
            out.append(ch)
            last_space = False
    return "".join(out)