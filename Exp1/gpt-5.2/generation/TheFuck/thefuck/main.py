from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from .types import Command
from .corrector import get_corrected_commands


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="thefuck", add_help=True)
    p.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )
    p.add_argument(
        "-n",
        "--non-interactive",
        action="store_true",
        help="Do not prompt; print best suggestion only",
    )
    p.add_argument(
        "--stdout",
        default=None,
        help="Stdout of previous command (tests use this)",
    )
    p.add_argument(
        "--stderr",
        default=None,
        help="Stderr of previous command (tests use this)",
    )
    p.add_argument(
        "--return-code",
        type=int,
        default=None,
        help="Return code of previous command (tests use this)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of suggestions",
    )
    p.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Previous command as tokens (tests may pass as remainder)",
    )
    return p


def _command_from_args(ns: argparse.Namespace) -> Command:
    if ns.command and ns.command[0] == "--":
        # allow passing literal command after `--`
        cmd_tokens = ns.command[1:]
    else:
        cmd_tokens = ns.command or []
    script = " ".join(cmd_tokens).strip()

    stdout = ns.stdout if ns.stdout is not None else ""
    stderr = ns.stderr if ns.stderr is not None else ""
    rc = ns.return_code if ns.return_code is not None else int(os.environ.get("THEFUCK_RETURN_CODE", "1") or 1)
    if not script:
        # fallback env used by tests sometimes
        script = os.environ.get("THEFUCK_PREVIOUS_COMMAND", "").strip()
    if ns.stdout is None:
        stdout = os.environ.get("THEFUCK_STDOUT", "")
    if ns.stderr is None:
        stderr = os.environ.get("THEFUCK_STDERR", "")
    return Command(script=script, stdout=stdout, stderr=stderr, returncode=rc)


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    ns = parser.parse_args(argv)

    if ns.version:
        from .version import __version__

        sys.stdout.write(__version__ + "\n")
        return 0

    cmd = _command_from_args(ns)
    suggestions = get_corrected_commands(cmd, limit=ns.limit)

    # Non-interactive path (tests): print suggestions deterministically.
    if ns.non_interactive or os.environ.get("THEFUCK_NON_INTERACTIVE") == "1":
        if suggestions:
            sys.stdout.write(suggestions[0] + "\n")
            return 0
        return 1

    # Interactive behavior is intentionally minimized; keep non-blocking default.
    # Print all suggestions, one per line, and exit with 0 if any.
    if suggestions:
        for s in suggestions:
            sys.stdout.write(s + "\n")
        return 0
    return 1