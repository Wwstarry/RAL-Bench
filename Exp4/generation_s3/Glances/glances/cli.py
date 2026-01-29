from __future__ import annotations

import argparse
import sys

from . import __version__
from .csvout import parse_fields, render_csv_line
from .errors import GlancesError, UnknownFieldError, UsageError
from .monitor import get_metrics


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="glances", add_help=True)
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="show program's version number and exit",
    )
    parser.add_argument(
        "--stdout-csv",
        metavar="FIELDS",
        help="one-shot CSV output with given comma-separated fields",
    )
    return parser.parse_args(argv)


def run_stdout_csv(fields_spec: str) -> str:
    fields = parse_fields(fields_spec)

    # Validate field names early so errors are predictable and non-empty.
    # resolve_field will also validate, but we want a consolidated message.
    supported = {"now", "cpu.user", "cpu.total", "mem.used", "load"}
    unknown = [f for f in fields if f not in supported]
    if unknown:
        if len(unknown) == 1:
            raise UnknownFieldError(f"Unknown field: {unknown[0]}")
        raise UnknownFieldError("Unknown fields: " + ", ".join(unknown))

    metrics = get_metrics()
    return render_csv_line(metrics, fields)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    try:
        ns = parse_args(argv)

        if ns.version:
            sys.stdout.write(f"glances {__version__}\n")
            return 0

        if ns.stdout_csv is not None:
            line = run_stdout_csv(ns.stdout_csv)
            # Exactly one record line; newline is fine.
            sys.stdout.write(line + "\n")
            return 0

        # If no actionable args provided, show help and exit non-zero? Upstream glances would run UI,
        # but non-goal here. Keep predictable: show help and exit 0.
        # Tests do not rely on this path.
        parse_args(["--help"])
        return 0

    except SystemExit as e:
        # argparse uses SystemExit for --help and parsing errors.
        # Preserve its exit code.
        code = e.code if isinstance(e.code, int) else 1
        return code
    except (UsageError, UnknownFieldError) as e:
        msg = str(e).strip() or "Invalid usage"
        sys.stderr.write(msg + "\n")
        return 1
    except GlancesError as e:
        msg = str(e).strip() or "Error"
        sys.stderr.write(msg + "\n")
        return 1