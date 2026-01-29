from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import __version__
from .csvout import stdout_csv_one_shot


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        # Ensure non-empty error message on stderr and non-zero exit.
        self.print_usage(sys.stderr)
        self.exit(2, f"error: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    p = _ArgumentParser(
        prog="glances",
        add_help=True,
        description="Minimal Glances-compatible CLI (subset).",
    )
    p.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Print version and exit",
    )
    p.add_argument(
        "--stdout-csv",
        metavar="FIELDS",
        nargs="?",
        help="One-shot CSV output for a comma-separated list of fields",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        sys.stdout.write(f"glances {__version__}\n")
        return 0

    if args.stdout_csv is not None:
        if args.stdout_csv == "" or args.stdout_csv is None:
            parser.error("--stdout-csv requires an argument")
        try:
            line = stdout_csv_one_shot(args.stdout_csv)
        except ValueError as e:
            msg = str(e).strip()
            if not msg:
                msg = "invalid --stdout-csv field(s)"
            sys.stderr.write(msg + "\n")
            return 2
        sys.stdout.write(line + "\n")
        return 0

    # No action specified: show help but exit non-zero for predictability?
    # The reference glances starts an interactive UI by default; we don't.
    # We keep predictable behavior: print help and exit non-zero.
    parser.print_help(sys.stdout)
    return 2