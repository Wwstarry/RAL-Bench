from __future__ import annotations

import argparse
import sys
from typing import Optional

from .types import Command
from .corrector import get_best_suggestion, get_suggestions


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="thefuck", add_help=True)
    p.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit.",
    )
    p.add_argument(
        "--stdout",
        default="",
        help="Stdout of previous command (for non-interactive/testing use).",
    )
    p.add_argument(
        "--stderr",
        default="",
        help="Stderr of previous command (for non-interactive/testing use).",
    )
    p.add_argument(
        "--return-code",
        type=int,
        default=1,
        help="Return code of previous command.",
    )
    p.add_argument(
        "--all",
        action="store_true",
        help="Print all suggestions (one per line).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        help="Ignored; present for compatibility.",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="Non-interactive mode; do not prompt.",
    )
    p.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Previous command (as tokens).",
    )
    return p


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    ns = parser.parse_args(argv)

    if ns.version:
        from .version import __version__

        sys.stdout.write(__version__ + "\n")
        return 0

    script = " ".join(ns.command).strip()
    cmd = Command(script=script, stdout=ns.stdout or "", stderr=ns.stderr or "", returncode=int(ns.return_code))

    if not script:
        # No previous command provided; behave benignly.
        return 0

    if ns.all:
        suggestions = get_suggestions(cmd)
        for s in suggestions:
            sys.stdout.write(s + "\n")
        return 0 if suggestions else 1

    best = get_best_suggestion(cmd)
    if best:
        sys.stdout.write(best + "\n")
        return 0
    return 1