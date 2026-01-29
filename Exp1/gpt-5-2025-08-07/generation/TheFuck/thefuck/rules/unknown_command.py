from __future__ import annotations

import os
import difflib
import shutil
from typing import Iterable, List, Tuple
from ..types import Command

name = "unknown_command"
priority = 100


def _list_executables() -> List[str]:
    seen = set()
    result: List[str] = []
    paths = os.environ.get("PATH", "").split(os.pathsep)
    for p in paths:
        if not p:
            continue
        try:
            for entry in os.listdir(p):
                if entry in seen:
                    continue
                full = os.path.join(p, entry)
                # On Windows, executables can have extensions; accept files
                if os.path.isfile(full) and os.access(full, os.X_OK):
                    seen.add(entry)
                    result.append(entry)
        except Exception:
            continue
    # Known common executables to help on minimal envs
    for extra in ("git", "python", "python3", "pip", "pip3", "docker", "kubectl", "ls", "cat", "grep", "make", "npm", "yarn"):
        if extra not in seen:
            result.append(extra)
    return result


def match(command: Command) -> bool:
    tokens = command.tokens
    if not tokens:
        return False
    cmd = tokens[0]
    # If it is already a known executable, no match
    if shutil.which(cmd):
        return False
    text = (command.stderr or command.stdout or "").lower()
    hints = (
        "command not found",
        "not recognized as an internal or external command",
        "did you mean",
        "is not recognized",
        "unknown command",
        "no such file or directory",
    )
    return any(h in text for h in hints) or (not shutil.which(cmd))


def suggest(command: Command) -> Iterable[Tuple[str, int]]:
    tokens = command.tokens
    if not tokens:
        return []
    cmd = tokens[0]
    rest = tokens[1:]
    candidates = _list_executables()
    # Try to find close matches
    matches = difflib.get_close_matches(cmd, candidates, n=5, cutoff=0.7)
    results: List[Tuple[str, int]] = []
    for m in matches:
        joined = " ".join([m] + rest)
        score = int(difflib.SequenceMatcher(a=cmd, b=m).ratio() * 100)
        results.append((joined, priority + score))
    # Some hardcoded common typos
    hardcoded = {
        "gti": "git",
        "pithon": "python",
        "pyhton": "python",
        "pipy": "pip",
        "dokcer": "docker",
        "kubeclt": "kubectl",
    }
    if cmd in hardcoded and hardcoded[cmd] not in matches:
        joined = " ".join([hardcoded[cmd]] + rest)
        results.append((joined, priority + 95))
    # Deduplicate preserving order
    seen = set()
    unique: List[Tuple[str, int]] = []
    for s, pr in results:
        if s not in seen:
            seen.add(s)
            unique.append((s, pr))
    return unique