from __future__ import annotations

import os
from typing import Iterable, Tuple, List
from ..types import Command

name = "grep_order"
priority = 60


def match(command: Command) -> bool:
    t = command.tokens
    if not t or t[0] != "grep":
        return False
    # We only handle simple "grep file pattern" vs "grep pattern file" without options
    # If options present, skip
    args = [a for a in t[1:] if not a.startswith("-")]
    if len(args) < 2:
        return False
    # If first arg is a file and second is not, suggest swap
    return os.path.exists(args[0]) and (not os.path.exists(args[1]))


def suggest(command: Command) -> Iterable[Tuple[str, int]]:
    t = command.tokens
    cmd = t[0]
    opts = [a for a in t[1:] if a.startswith("-")]
    args = [a for a in t[1:] if not a.startswith("-")]
    file_arg, pattern_arg = args[0], args[1]
    new = " ".join([cmd] + opts + [pattern_arg, file_arg] + args[2:])
    return [(new, priority + 10)]