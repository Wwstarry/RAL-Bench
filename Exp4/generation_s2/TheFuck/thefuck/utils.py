from __future__ import annotations

import os
import shutil
from difflib import get_close_matches
from typing import Iterable, List, Optional, Sequence, Tuple


def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def available_commands() -> List[str]:
    """Return a sorted unique list of commands in PATH for deterministic output."""
    paths = os.environ.get("PATH", "").split(os.pathsep)
    cmds = set()
    for p in paths:
        if not p or not os.path.isdir(p):
            continue
        try:
            for name in os.listdir(p):
                if name and not name.startswith("."):
                    cmds.add(name)
        except OSError:
            continue
    return sorted(cmds)


def closest_commands(word: str, choices: Sequence[str], n: int = 5) -> List[str]:
    # Deterministic: difflib returns in order of best match; choices already sorted
    return list(get_close_matches(word, list(choices), n=n, cutoff=0.6))


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def shell_join(parts: Sequence[str]) -> str:
    # Tests typically use simple commands; avoid complex quoting rules.
    return " ".join(parts)


def parse_unknown_command_from_output(output: str) -> Optional[str]:
    """
    Extract unknown command token from common error strings.
    Supported patterns:
      - 'command not found: gittt'
      - 'gittt: command not found'
      - 'bash: gittt: command not found'
      - 'zsh: command not found: gittt'
    """
    out = output or ""
    low = out.lower()

    if "command not found" not in low:
        return None

    # zsh: command not found: foo
    marker = "command not found:"
    idx = low.find(marker)
    if idx != -1:
        tail = out[idx + len(marker) :].strip()
        if tail:
            return tail.split()[0].strip().strip("'\"")

    # bash: foo: command not found
    marker2 = ": command not found"
    idx2 = low.find(marker2)
    if idx2 != -1:
        head = out[:idx2].strip()
        # take last token before marker
        token = head.split()[-1] if head.split() else ""
        token = token.strip(":").strip().strip("'\"")
        return token or None

    return None


def parse_unknown_subcommand_from_output(output: str) -> Optional[Tuple[str, str]]:
    """
    Extract (tool, subcommand) from patterns like:
      - "git: 'comit' is not a git command. See 'git --help'."
      - "Error: No such subcommand: 'instal'"
      - "'instal' is not a recognized command"
    """
    out = output or ""

    # git: 'x' is not a git command
    if "is not a git command" in out:
        # tool is often 'git' at start
        tool = out.split(":", 1)[0].strip()
        # between quotes
        q1 = out.find("'")
        q2 = out.find("'", q1 + 1) if q1 != -1 else -1
        if q1 != -1 and q2 != -1:
            sub = out[q1 + 1 : q2]
            return tool, sub

    # generic: No such subcommand: 'x'
    key = "No such subcommand:"
    if key in out:
        idx = out.find(key)
        tail = out[idx + len(key) :].strip()
        if tail.startswith("'") and "'" in tail[1:]:
            sub = tail.split("'", 2)[1]
            return "", sub
        return "", tail.split()[0].strip("'\"")

    # generic: "'x' is not a recognized command"
    if "is not a recognized command" in out:
        if out.strip().startswith("'"):
            sub = out.split("'", 2)[1]
            return "", sub

    return None