from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .csvout import collect_row, format_csv_row, parse_fields
from .errors import GlancesError
from .version import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="glances", add_help=True)
    p.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"Glances {__version__}",
        help="Print version and exit.",
    )
    p.add_argument(
        "--stdout-csv",
        metavar="FIELDS",
        help="Output one CSV row with the specified comma-separated fields, then exit.",
    )
    return p


def _err(msg: str) -> None:
    sys.stderr.write(str(msg).rstrip() + "\n")


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.stdout_csv is None:
        # Minimal subset requires explicit action; do not start interactive UI.
        parser.print_help(sys.stderr)
        return 2

    try:
        fields = parse_fields(args.stdout_csv)
        values = collect_row(fields)
        line = format_csv_row(values)
        sys.stdout.write(line + "\n")
        return 0
    except GlancesError as e:
        _err(str(e) if str(e).strip() else "Error")
        return 1