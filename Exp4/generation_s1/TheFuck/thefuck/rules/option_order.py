from __future__ import annotations

import re

from ..types import Command, Rule
from ..utils import best_by_distance, extract_usage_options, join_command


_RE_UNKNOWN_OPT = re.compile(r"(unknown option|unrecognized arguments)\s*[:]?(.+)?", re.IGNORECASE)


def _match(command: Command) -> bool:
    if command.return_code == 0:
        return False
    s = command.stderr or ""
    return bool(_RE_UNKNOWN_OPT.search(s))


def _get_new_command(command: Command) -> list[str]:
    parts = command.parts
    if not parts:
        return []

    s = command.stderr or ""
    # Try to locate an "unknown option" token like "--hepl"
    m = re.search(r"(?<!\w)(--[A-Za-z0-9][A-Za-z0-9_-]*|-[A-Za-z0-9])", s)
    bad = m.group(1) if m else None
    if not bad:
        # Fallback: find any token in the command that looks like an option and is suspiciously close to --help.
        for t in parts:
            if t.startswith("--") or (t.startswith("-") and len(t) == 2):
                bad = t
                break
    if not bad:
        return []

    opts = extract_usage_options(s)
    if not opts:
        # Conservative default choices.
        opts = ["--help", "--version", "-h"]

    best = best_by_distance(bad, opts, max_dist=2)
    if not best or best == bad:
        return []

    # Replace first occurrence of bad in the command parts.
    new_parts = []
    replaced = False
    for t in parts:
        if not replaced and t == bad:
            new_parts.append(best)
            replaced = True
        else:
            new_parts.append(t)
    if not replaced:
        return []
    return [join_command(new_parts)]


rule = Rule(
    name="option_order",
    match=_match,
    get_new_command=_get_new_command,
    priority=150,
)