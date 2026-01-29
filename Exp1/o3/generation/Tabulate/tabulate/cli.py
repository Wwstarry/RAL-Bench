#!/usr/bin/env python
"""
A trimmed-down command line interface for the lightweight ``tabulate`` re-implementation.

The feature set is smaller than the original ``tabulate`` script but it is
good enough for quick tests:

    $ python -m tabulate.cli --format grid file.tsv
"""
from __future__ import annotations

import argparse
import csv
import sys

from .core import tabulate
from .formats import TABLE_FORMATS


def _read_stdin(delimiter: str):
    data = []
    for row in csv.reader(sys.stdin, delimiter=delimiter):
        data.append(row)
    return data


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Pretty-print tabular data.")
    parser.add_argument(
        "-f",
        "--format",
        default="simple",
        choices=sorted(TABLE_FORMATS.keys()),
        help="table format",
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        default=",",
        help="CSV/TSV delimiter when reading from stdin (default: ',')",
    )
    parser.add_argument(
        "-H",
        "--headers",
        action="store_true",
        help="treat first row as header",
    )
    args = parser.parse_args(argv)

    data = _read_stdin(args.delimiter)
    if args.headers and data:
        headers = data[0]
        data = data[1:]
    else:
        headers = ()

    print(tabulate(data, headers=headers, tablefmt=args.format))


if __name__ == "__main__":
    main()