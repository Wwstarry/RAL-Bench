from __future__ import annotations

import os
import difflib
from typing import Iterable, List, Tuple
from ..types import Command

name = "cd"
priority = 80


def match(command: Command) -> bool:
    t = command.tokens
    if not t or t[0] != "cd":
        return False
    if len(t) < 2:
        return False
    path = t[1]
    # Expand ~
    path = os.path.expanduser(path)
    if os.path.isdir(path):
        return False
    # Stderr hints
    txt = (command.stderr or command.stdout or "").lower()
    hints = ("no such file or directory", "cannot find the path specified", "not found")
    return any(h in txt for h in hints) or not os.path.isdir(path)


def _candidate_dirs(base: str) -> List[str]:
    try:
        entries = os.listdir(base or ".")
    except Exception:
        entries = []
    dirs = [e for e in entries if os.path.isdir(os.path.join(base or ".", e))]
    return dirs


def suggest(command: Command) -> Iterable[Tuple[str, int]]:
    t = command.tokens
    _, raw_path, *rest = t
    rest_part = " ".join(rest) if rest else ""
    path = os.path.expanduser(raw_path)
    base_dir = ""
    frag = path
    if os.path.sep in path:
        base_dir = os.path.dirname(path)
        frag = os.path.basename(path)
    candidates = _candidate_dirs(base_dir or ".")
    matches = difflib.get_close_matches(frag, candidates, n=5, cutoff=0.5)
    suggestions: List[Tuple[str, int]] = []
    for m in matches:
        corrected = os.path.join(base_dir, m) if base_dir else m
        new_script = "cd " + corrected
        if rest_part:
            new_script += " " + rest_part
        score = int(difflib.SequenceMatcher(a=frag, b=m).ratio() * 100)
        suggestions.append((new_script, priority + score))
    return suggestions