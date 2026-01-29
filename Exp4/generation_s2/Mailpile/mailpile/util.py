import re
import time
from typing import Any, Iterable, Optional

B36_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
_B36_MAP = {c: i for i, c in enumerate(B36_ALPHABET)}


def b36(n: int) -> str:
    """Convert an integer to base36 (lowercase)."""
    if n is None:
        raise TypeError("b36() requires an integer")
    if n == 0:
        return "0"
    if n < 0:
        return "-" + b36(-n)
    out = []
    while n:
        n, r = divmod(n, 36)
        out.append(B36_ALPHABET[r])
    return "".join(reversed(out))


def unb36(s: str) -> int:
    """Convert base36 string to integer."""
    if s is None:
        raise TypeError("unb36() requires a string")
    s = str(s).strip().lower()
    if not s:
        raise ValueError("Empty base36 value")
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    n = 0
    for ch in s:
        if ch not in _B36_MAP:
            raise ValueError("Invalid base36 character: %r" % ch)
        n = n * 36 + _B36_MAP[ch]
    return -n if neg else n


_WS_RE = re.compile(r"\s+", re.UNICODE)


def CleanText(s: Any, maxlen: Optional[int] = None) -> str:
    """
    Normalize arbitrary input to a safe-ish single-line string:
    - convert to str
    - replace CR/LF/TAB with spaces
    - collapse whitespace
    - strip
    - optionally truncate
    """
    if s is None:
        s = ""
    if isinstance(s, bytes):
        s = s.decode("utf-8", "replace")
    else:
        s = str(s)
    s = s.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    s = _WS_RE.sub(" ", s).strip()
    if maxlen is not None and maxlen >= 0 and len(s) > maxlen:
        s = s[:maxlen]
    return s


def elapsed_timestamp(ts: Optional[float] = None) -> str:
    """
    Return a compact, deterministic timestamp string used in logs/ids.
    """
    if ts is None:
        ts = time.time()
    # Milliseconds, base36, for compactness.
    ms = int(ts * 1000)
    return b36(ms)


def dict_merge(*dicts: dict) -> dict:
    out = {}
    for d in dicts:
        if d:
            out.update(d)
    return out


def uniq(seq: Iterable[Any]) -> list:
    """Stable unique of a sequence."""
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out