from __future__ import annotations

import argparse
import sys
from typing import Optional, List
from .types import Command
from .corrector import get_suggestions


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="thefuck",
        description="Auto-correct your previous console command (minimal implementation).",
        add_help=True,
    )
    p.add_argument("command", nargs="?", help="The command to correct (quote it if it contains spaces).")
    p.add_argument("--stdout", default="", help="Captured stdout of the previous command.")
    p.add_argument("--stderr", default="", help="Captured stderr of the previous command.")
    p.add_argument("--return-code", "-r", type=int, default=0, help="Return code of the previous command.")
    p.add_argument("--all", action="store_true", help="Print all suggestions instead of only the best one.")
    p.add_argument("--version", action="store_true", help="Show version and exit.")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    from . import __version__

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if not args.command:
        parser.print_usage(sys.stderr)
        return 2

    cmd = Command(script=args.command, stdout=args.stdout, stderr=args.stderr, return_code=args.return_code)
    suggestions = get_suggestions(cmd)

    if not suggestions:
        # No suggestions found
        return 1

    if args.all:
        for s in suggestions:
            print(s.script)
    else:
        # print the best one
        print(suggestions[0].script)

    return 0