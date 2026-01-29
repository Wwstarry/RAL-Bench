"""
CLI entrypoint for the minimal glances-compatible tool.

Usage examples:
- python -m glances --help
- python -m glances -V
- python -m glances --version
- python -m glances --stdout-csv now,cpu.user,mem.used,load
"""

from __future__ import annotations

import argparse
import sys
from typing import List

from . import __version__
from .metrics import (
    get_now,
    get_cpu_user_percent,
    get_cpu_total_percent,
    get_mem_used_bytes,
    get_load_avg1,
)


SUPPORTED_FIELDS = {
    "now",
    "cpu.user",
    "cpu.total",
    "mem.used",
    "load",
}


def _compute_field_value(field: str) -> str:
    """Compute the CSV value string for a single field."""
    if field == "now":
        return str(get_now())
    elif field == "cpu.user":
        return str(get_cpu_user_percent())
    elif field == "cpu.total":
        return str(get_cpu_total_percent())
    elif field == "mem.used":
        return str(get_mem_used_bytes())
    elif field == "load":
        return str(get_load_avg1())
    else:
        raise ValueError(f"Unknown field: {field}")


def _stdout_csv(fields_str: str) -> int:
    """Handle one-shot CSV output for given fields string. Return exit code."""
    fields = [f.strip() for f in fields_str.split(",") if f.strip() != ""]
    if not fields:
        print("Error: No fields specified for --stdout-csv.", file=sys.stderr)
        return 2
    # Validate fields first
    for f in fields:
        if f not in SUPPORTED_FIELDS:
            print(f"Error: Unknown field: {f}", file=sys.stderr)
            return 2
    # Compute values
    try:
        values: List[str] = [_compute_field_value(f) for f in fields]
    except Exception as e:
        msg = str(e).strip() or "Error while computing fields."
        print(msg, file=sys.stderr)
        return 2
    # Print single CSV line
    print(",".join(values))
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="glances",
        description="Minimal glances-compatible CLI for system monitoring (one-shot CSV).",
        add_help=True,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Print version and exit.",
    )
    parser.add_argument(
        "--stdout-csv",
        metavar="FIELDS",
        help="Comma-separated fields to output as a single CSV line. Supported: now,cpu.user,cpu.total,mem.used,load",
    )

    args = parser.parse_args(argv)

    if args.version:
        print(f"Glances {__version__}")
        return 0

    if args.stdout_csv is not None:
        return _stdout_csv(args.stdout_csv)

    # If no actionable option provided, show help and exit non-zero to indicate invalid invocation.
    parser.print_help(sys.stdout)
    return 2


if __name__ == "__main__":
    sys.exit(main())