import errno
import hashlib
import json
import os
import re
import time
from typing import Any


_CONTROL_DEFAULT_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def CleanText(text, banned=None, replacement: str = '', collapse_whitespace: bool = True) -> str:
    """
    Remove/replace unsafe characters and normalize whitespace.

    - If text is None => ''
    - If banned is None: remove ASCII control chars except tab/newline/CR, and DEL.
    - If banned is iterable/string: replace any of those characters with replacement.
    - If banned is callable: called per-character; if True => replace.
    """
    if text is None:
        text = ''
    if not isinstance(text, str):
        text = str(text)

    if banned is None:
        text = _CONTROL_DEFAULT_RE.sub(replacement, text)
    else:
        if callable(banned):
            text = ''.join((replacement if banned(ch) else ch) for ch in text)
        else:
            banned_set = set(banned)
            text = ''.join((replacement if ch in banned_set else ch) for ch in text)

    if collapse_whitespace:
        text = re.sub(r'\s+', ' ', text).strip()

    return text


_B36_ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyz'
_B36_MAP = {c: i for i, c in enumerate(_B36_ALPHABET)}


def b36(num: int) -> str:
    if not isinstance(num, int):
        raise TypeError('b36 expects int')
    if num < 0:
        raise ValueError('b36 expects non-negative int')
    if num == 0:
        return '0'
    n = num
    out = []
    while n:
        n, r = divmod(n, 36)
        out.append(_B36_ALPHABET[r])
    return ''.join(reversed(out))


def intb36(s: str) -> int:
    if s is None:
        raise ValueError('Invalid base36')
    if not isinstance(s, str):
        s = str(s)
    t = s.strip().lower()
    if t == '':
        raise ValueError('Invalid base36')
    val = 0
    for ch in t:
        if ch not in _B36_MAP:
            raise ValueError('Invalid base36')
        val = val * 36 + _B36_MAP[ch]
    return val


def strhash(s, length: int = 8) -> str:
    """
    Deterministic hash -> lowercase base36 string of exactly `length` chars.
    """
    if s is None:
        s = ''
    if isinstance(s, str):
        b = s.encode('utf-8', 'replace')
    elif isinstance(s, (bytes, bytearray)):
        b = bytes(s)
    else:
        b = str(s).encode('utf-8', 'replace')

    # Use SHA1 for determinism and availability.
    digest = hashlib.sha1(b).digest()
    num = int.from_bytes(digest, 'big')
    out = b36(num)

    if len(out) < length:
        out = ('0' * (length - len(out))) + out
    return out[-length:]


def safe_remove(path: str) -> bool:
    try:
        os.remove(path)
        return True
    except FileNotFoundError:
        return False
    except OSError as e:
        if e.errno == errno.ENOENT:
            return False
        raise


def safe_mkdirs(path: str, mode: int = 0o700) -> None:
    if not path:
        return
    # exist_ok=True prevents raising if already exists.
    os.makedirs(path, mode=mode, exist_ok=True)


def json_helper(obj: Any):
    """
    Helper for json.dumps(default=...).
    """
    if hasattr(obj, '__json__') and callable(getattr(obj, '__json__')):
        return obj.__json__()
    if isinstance(obj, (bytes, bytearray)):
        return bytes(obj).decode('utf-8', 'replace')
    if isinstance(obj, (set, tuple)):
        return list(obj)
    raise TypeError('%r is not JSON serializable' % (type(obj),))


class TimedCache(object):
    def __init__(self, ttl: float = 60.0):
        self.ttl = float(ttl)
        self._data = {}  # key -> (expires_at, value)

    def expire(self) -> None:
        now = time.time()
        dead = [k for k, (exp, _v) in self._data.items() if exp <= now]
        for k in dead:
            self._data.pop(k, None)

    def set(self, key, value) -> None:
        self._data[key] = (time.time() + self.ttl, value)

    def get(self, key, default=None):
        self.expire()
        item = self._data.get(key)
        if not item:
            return default
        exp, val = item
        if exp <= time.time():
            self._data.pop(key, None)
            return default
        return val

    def __contains__(self, key) -> bool:
        self.expire()
        item = self._data.get(key)
        if not item:
            return False
        exp, _val = item
        if exp <= time.time():
            self._data.pop(key, None)
            return False
        return True