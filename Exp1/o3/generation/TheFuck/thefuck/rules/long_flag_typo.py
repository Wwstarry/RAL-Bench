"""
Handles simple *long option* typos by looking at the tool's `--help` text.

Example:
    $ python --versoin
    error: unrecognized arguments: --versoin
Would suggest:
    python --version
"""
from __future__ import annotations

import re
import subprocess

from ..command import Command
from ..utils import closest_command

priority = 300


def _extract_invalid_flag(stderr: str) -> str | None:
    """
    Try to extract the *unknown/invalid* option from stderr.
    Works with several popular error message styles.
    """
    patterns = [
        r"unrecognized option ['\"]?(-{1,2}[A-Za-z0-9_\-]+)['\"]?",  # GNU getopt
        r"unknown (?:option|flag):\s*(['\"]?-{1,2}[A-Za-z0-9_\-]+['\"]?)",
        r"invalid option -- '([A-Za-z0-9_\-]+)'",
    ]
    for pat in patterns:
        m = re.search(pat, stderr, flags=re.IGNORECASE)
        if m:
            grp = m.group(1)
            # pattern might include surrounding quotes
            return grp.strip("'\"")
    return None


def _known_long_flags(executable: str) -> list[str]:
    """
    Ask the executable for its help text and extract strings that *look* like
    long options (``--something``).  Incredibly naive, but suffices for the
    modest requirements of this kata.
    """
    try:
        completed = subprocess.run(
            [executable, "--help"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=1.5,
        )
    except Exception:
        return []
    text = completed.stdout or ""
    return sorted(set(re.findall(r"--[A-Za-z0-9][A-Za-z0-9_\-]*", text)))


def match(command: Command) -> bool:
    if not command.stderr:
        return False
    return _extract_invalid_flag(command.stderr) is not None


def get_new_command(command: Command):
    invalid_flag = _extract_invalid_flag(command.stderr or "")
    if not invalid_flag:
        return []
    exe = command.parts[0]
    suggestions = _known_long_flags(exe)
    if not suggestions:
        return []
    close = closest_command(invalid_flag, )  # Re-using helper for flags too
    # difflib tends to include the original string itself – remove it.
    close = [c for c in close if c != invalid_flag]
    if not close:
        return []
    # Build new command lines
    tail = command.parts[1:]
    # Remove *invalid_flag* if present in tail (so we can replace it cleanly)
    tail = [tok for tok in tail if tok != invalid_flag]
    corrected = [f"{exe} {candidate} {' '.join(tail)}".rstrip() for candidate in close]
    return corrected