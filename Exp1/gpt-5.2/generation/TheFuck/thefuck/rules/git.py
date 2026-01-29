from __future__ import annotations

import difflib
import re
from typing import Iterable, List, Optional

from .base import Rule
from ..types import Command

_GIT_SUBCOMMANDS = [
    "add",
    "bisect",
    "branch",
    "checkout",
    "clone",
    "commit",
    "diff",
    "fetch",
    "init",
    "log",
    "merge",
    "mv",
    "pull",
    "push",
    "rebase",
    "reset",
    "restore",
    "rm",
    "show",
    "status",
    "tag",
]


def _unknown_subcommand(cmd: Command) -> Optional[str]:
    if cmd.command != "git":
        return None
    out = cmd.output
    # Typical git error: "git: 'statsu' is not a git command. See 'git --help'."
    m = re.search(r"git:\s+'([^']+)'\s+is not a git command", out, flags=re.I)
    if m:
        return m.group(1)
    # Another: "Unknown subcommand: ..."
    m = re.search(r"unknown (?:subcommand|command)\s*[:]\s*([^\s]+)", out, flags=re.I)
    if m:
        return m.group(1)
    # If second token exists and command failed with help suggestion.
    if cmd.returncode != 0 and len(cmd.script_parts) >= 2 and "git" in out.lower():
        if "not a git command" in out.lower():
            return cmd.script_parts[1]
    return None


class GitUnknownSubcommand(Rule):
    name = "git_unknown_subcommand"
    priority = 5

    def match(self, command: Command) -> bool:
        return _unknown_subcommand(command) is not None

    def get_new_command(self, command: Command) -> Iterable[str]:
        bad = _unknown_subcommand(command)
        if not bad:
            return []
        best = difflib.get_close_matches(bad, _GIT_SUBCOMMANDS, n=3, cutoff=0.6)
        parts = command.script_parts
        out: List[str] = []
        for cand in best:
            new_parts = parts[:]
            if len(new_parts) >= 2:
                new_parts[1] = cand
            else:
                new_parts += [cand]
            out.append(" ".join(new_parts))
        return out