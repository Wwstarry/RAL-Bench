from __future__ import annotations

import os
import difflib
from typing import Iterable, Tuple, List
from ..types import Command

name = "no_such_file"
priority = 50

_FILE_CMDS = {"cat", "ls", "rm", "mv", "cp", "python", "python3", "head", "tail"}


def match(command: Command) -> bool:
    t = command.tokens
    if not t:
        return False
    cmd = t[0]
    if cmd not in _FILE_CMDS:
        # Generic fallback for common file-targeting commands
        txt = (command.stderr or command.stdout or "").lower()
        if "no such file or directory" not in txt:
            return False
    # Identify a non-option argument that doesn't exist
    for tok in reversed(t[1:]):
        if tok.startswith("-"):
            continue
        # Expand user and env
        path = os.path.expanduser(os.path.expandvars(tok))
        if not os.path.exists(path):
            return True
        break
    return False


def suggest(command: Command) -> Iterable[Tuple[str, int]]:
    t = command.tokens
    # Find the last non-option token as the likely file
    target_idx = None
    for i in range(len(t) - 1, 0, -1):
        if not t[i].startswith("-"):
            target_idx = i
            break
    if target_idx is None:
        return []
    target = t[target_idx]
    base_dir = "."
    frag = target
    if os.path.sep in target:
        base_dir = os.path.dirname(target) or "."
        frag = os.path.basename(target)
    try:
        entries = os.listdir(base_dir)
    except Exception:
        entries = []
    # Only consider visible files similar to frag
    candidates = [e for e in entries if not e.startswith(".")]
    matches = difflib.get_close_matches(frag, candidates, n=5, cutoff=0.5)
    suggestions: List[Tuple[str, int]] = []
    for m in matches:
        corrected = os.path.join(base_dir, m) if base_dir and base_dir != "." else m
        new_tokens = list(t)
        new_tokens[target_idx] = corrected
        new = " ".join(new_tokens)
        score = int(difflib.SequenceMatcher(a=frag, b=m).ratio() * 100)
        suggestions.append((new, priority + score))
    return suggestions