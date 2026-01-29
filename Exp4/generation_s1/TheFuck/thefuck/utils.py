from __future__ import annotations

import re
import shlex
from functools import lru_cache
from typing import Iterable


def split_command(command: str) -> list[str]:
    command = command or ""
    try:
        return shlex.split(command, posix=True)
    except Exception:
        return command.split()


def join_command(parts: Iterable[str]) -> str:
    # Minimal stable join: keep it simple and deterministic.
    return " ".join(str(p) for p in parts if p is not None and str(p) != "")


def unique_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    # DP with two rows
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def best_by_distance(target: str, candidates: Iterable[str], max_dist: int) -> str | None:
    target = target or ""
    best = None
    best_d = None
    for c in candidates:
        d = levenshtein(target, c)
        if d <= max_dist:
            if best is None or d < best_d or (d == best_d and c < best):
                best = c
                best_d = d
    return best


_COMMAND_NOT_FOUND_PATTERNS = [
    re.compile(r"command not found", re.IGNORECASE),
    re.compile(r"not recognized as an internal or external command", re.IGNORECASE),
    re.compile(r"no such file or directory", re.IGNORECASE),
]


def looks_like_command_not_found(stderr: str) -> bool:
    s = stderr or ""
    return any(p.search(s) for p in _COMMAND_NOT_FOUND_PATTERNS)


@lru_cache(maxsize=1)
def default_known_commands() -> tuple[str, ...]:
    # Small deterministic vocabulary used by rules.
    return (
        "git",
        "pip",
        "python",
        "python3",
        "ls",
        "cd",
        "cat",
        "echo",
        "mkdir",
        "rm",
        "pwd",
        "grep",
    )


def extract_usage_options(stderr: str) -> list[str]:
    """
    Try to extract option tokens from typical argparse usage/help text.
    Conservative: return only obvious -x / --long options.
    """
    s = stderr or ""
    opts = set(re.findall(r"(?<!\w)(--[A-Za-z0-9][A-Za-z0-9_-]*)", s))
    opts.update(re.findall(r"(?<!\w)(-[A-Za-z0-9])", s))
    return sorted(opts)