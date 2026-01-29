"""
Lightweight command-line interface exposing a *very* reduced subset
of the real Glances CLI.

Usage examples
--------------
python -m glances --help
python -m glances -V
python -m glances --stdout-csv now,cpu.user,mem.used,load
"""

from __future__ import annotations

import argparse
import sys
from typing import List

from . import __version__
from .core import collect_metrics, supported_fields


def _build_arg_parser() -> argparse.ArgumentParser:
    """
    Create and configure the top level argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="glances",
        description=(
            "Minimal, self-contained system monitoring CLI exposing "
            "a subset of the original Glances interface."
        ),
        add_help=True,
    )

    # Version flag.
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Print the program version and exit.",
    )

    # One-shot CSV output.
    parser.add_argument(
        "--stdout-csv",
        metavar="FIELDS",
        help=(
            "Comma-separated list of field names to output as a single CSV line. "
            "Supported fields: " + ", ".join(sorted(supported_fields()))
        ),
    )

    return parser


def _handle_stdout_csv(fields_spec: str) -> None:
    """
    Process `--stdout-csv` requests.

    Parameters
    ----------
    fields_spec
        A comma-separated list of field identifiers.
    """
    fields: List[str] = [f.strip() for f in fields_spec.split(",") if f.strip()]

    # Validate requested fields.
    unknown = [f for f in fields if f not in supported_fields()]
    if unknown:
        print(f"Error: Unsupported field(s): {', '.join(unknown)}", file=sys.stderr)
        sys.exit(1)

    metrics = collect_metrics()

    # Extract in requested order, stringify, and emit a single CSV line.
    try:
        values = [metrics[f] for f in fields]
    except KeyError as exc:  # pragma: no cover
        # This should not happen due to validation, but we stay defensive.
        print(f"Internal error: missing metric {exc!s}", file=sys.stderr)
        sys.exit(1)

    # Convert all values to string while keeping numeric representation intact.
    output = ",".join(str(v) for v in values)
    print(output)
    sys.exit(0)


def main(argv: List[str] | None = None) -> None:  # noqa: D401
    """
    Entrypoint for the CLI – parse arguments and dispatch.
    """
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    # Handle `--version` early and exit.
    if args.version:
        print(__version__)
        sys.exit(0)

    # Handle `--stdout-csv`.
    if args.stdout_csv is not None:
        _handle_stdout_csv(args.stdout_csv)

    # No actionable arguments – default to help.
    parser.print_help(sys.stderr)
    sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    # When executed as a module with `python -m glances`.
    main()