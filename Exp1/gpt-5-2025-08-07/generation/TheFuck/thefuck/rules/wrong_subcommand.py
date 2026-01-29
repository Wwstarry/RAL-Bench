from __future__ import annotations

import difflib
from typing import Iterable, List, Tuple, Dict, Set
from ..types import Command

name = "wrong_subcommand"
priority = 90

_SUBCMDS: Dict[str, Set[str]] = {
    "git": {
        "add", "branch", "checkout", "clone", "commit", "diff", "fetch", "init", "log",
        "merge", "mv", "pull", "push", "rebase", "remote", "reset", "rm", "show", "status",
        "stash", "tag",
    },
    "pip": {"install", "uninstall", "freeze", "list", "show", "search", "wheel", "download"},
    "docker": {"build", "pull", "push", "run", "images", "ps", "exec", "logs", "compose"},
    "kubectl": {"get", "describe", "apply", "delete", "create", "logs", "exec", "config", "rollout"},
    "npm": {"install", "uninstall", "run", "init", "publish", "test"},
    "yarn": {"add", "remove", "run", "init"},
    "conda": {"install", "remove", "create", "list", "update", "search"},
}


def match(command: Command) -> bool:
    t = command.tokens
    if len(t) < 2:
        return False
    base = t[0]
    sub = t[1]
    if base not in _SUBCMDS:
        return False
    # Already valid?
    if sub in _SUBCMDS[base]:
        return False
    # Likely failure if return_code != 0 or stderr contains unknown command hints
    txt = (command.stderr or command.stdout or "").lower()
    if any(h in txt for h in ("unknown command", "did you mean", "is not a", "is not a git command", "unknown subcommand")):
        return True
    # Fallback: attempt correction if it's close to a known subcommand
    possible = difflib.get_close_matches(sub, list(_SUBCMDS[base]), n=1, cutoff=0.7)
    return bool(possible)


def suggest(command: Command) -> Iterable[Tuple[str, int]]:
    t = command.tokens
    base, sub, *rest = t
    options = list(_SUBCMDS.get(base, []))
    matches = difflib.get_close_matches(sub, options, n=3, cutoff=0.6)
    results: List[Tuple[str, int]] = []
    for m in matches:
        new = " ".join([base, m] + rest)
        score = int(difflib.SequenceMatcher(a=sub, b=m).ratio() * 100)
        results.append((new, priority + score))
    # Deduplicate
    seen = set()
    uniq: List[Tuple[str, int]] = []
    for s, p in results:
        if s not in seen:
            seen.add(s)
            uniq.append((s, p))
    return uniq