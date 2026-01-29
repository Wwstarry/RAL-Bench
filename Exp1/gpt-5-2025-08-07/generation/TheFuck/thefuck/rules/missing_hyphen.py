from __future__ import annotations

from typing import Iterable, Tuple, List
from ..types import Command

name = "missing_hyphen"
priority = 55


def match(command: Command) -> bool:
    t = command.tokens
    if len(t) < 3:
        return False
    # Known patterns: git commit m -> -m
    if t[0] == "git" and t[1] == "commit" and "m" in t[2:]:
        return True
    # pip install r -> -r
    if t[0] in ("pip", "pip3") and t[1] == "install" and "r" in t[2:]:
        return True
    return False


def suggest(command: Command) -> Iterable[Tuple[str, int]]:
    t = command.tokens
    new_tokens = list(t)
    if t[0] == "git" and t[1] == "commit":
        new_tokens = [tok if tok != "m" else "-m" for tok in new_tokens]
    if t[0] in ("pip", "pip3") and t[1] == "install":
        new_tokens = [tok if tok != "r" else "-r" for tok in new_tokens]
    return [(" ".join(new_tokens), priority + 10)]