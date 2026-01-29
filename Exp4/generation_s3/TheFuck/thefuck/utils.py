from __future__ import annotations

import re
import shlex
from typing import Iterable


def shell_split(s: str) -> list[str]:
    """Deterministic shell-like split."""
    s = s or ""
    try:
        return shlex.split(s, posix=True)
    except ValueError:
        # If unbalanced quotes etc., fall back to a simple whitespace split.
        return s.split()


def quote(s: str) -> str:
    """Conservative quoting for POSIX shells."""
    return shlex.quote(s)


def shell_join(args: list[str]) -> str:
    """Deterministic join using shlex quoting rules."""
    return " ".join(quote(a) for a in args)


def unique_stable(seq: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for x in seq:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def levenshtein(a: str, b: str) -> int:
    """Classic Levenshtein distance, deterministic, no third-party deps."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    # Ensure a is the longer string for a smaller DP row.
    if len(a) < len(b):
        a, b = b, a

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            insert = cur[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            cur.append(min(insert, delete, sub))
        prev = cur
    return prev[-1]


_ERROR_PATTERNS = [
    re.compile(r"command not found", re.IGNORECASE),
    re.compile(r"not recognized as an internal or external command", re.IGNORECASE),
    re.compile(r"No such file or directory", re.IGNORECASE),
    re.compile(r"Unknown command", re.IGNORECASE),
]


def contains_command_not_found(text: str) -> bool:
    text = text or ""
    return any(p.search(text) for p in _ERROR_PATTERNS)


def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())