from __future__ import annotations

import argparse
import sys
from typing import List

from . import __version__
from .csvout import csv_one_shot
from .exceptions import GlancesError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="glances",
        add_help=True,
        description="Minimal Glances-compatible CLI (subset) for one-shot CSV output.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="print version and exit",
    )
    parser.add_argument(
        "--stdout-csv",
        dest="stdout_csv",
        metavar="FIELDS",
        help="print one CSV line to stdout with given comma-separated fields and exit",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    if argv is None:
        argv = []

    parser = _build_parser()

    # argparse already handles --help with exit code 0
    args = parser.parse_args(argv)

    if args.version:
        sys.stdout.write(f"glances {__version__}\n")
        return 0

    if args.stdout_csv is None:
        # Predictable failure for missing invocation.
        sys.stderr.write("error: --stdout-csv requires an argument\n")
        return 2

    try:
        line = csv_one_shot(args.stdout_csv)
    except GlancesError as e:
        msg = str(e).strip()
        if not msg:
            msg = "error"
        sys.stderr.write(msg + "\n")
        return 2

    sys.stdout.write(line + "\n")
    return 0