from __future__ import annotations

import argparse
import csv
import sys
from typing import List, Optional

from .core import tabulate
from .formats import tabulate_formats


def _read_delimited(
    fp,
    delimiter: str,
    has_header: bool,
) -> (List[List[str]], Optional[List[str]]):
    reader = csv.reader(fp, delimiter=delimiter)
    rows = list(reader)
    if not rows:
        return [], [] if has_header else None
    if has_header:
        return rows[1:], rows[0]
    return rows, None


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="tabulate", add_help=True)
    p.add_argument("--format", "-f", default="simple", choices=sorted(tabulate_formats.keys()) + ["csv", "tsv"])
    p.add_argument("--separator", "-s", default=None, help="Input delimiter (default: auto for csv/tsv else tab).")
    p.add_argument("--header", action="store_true", help="Treat first row as header.")
    p.add_argument("--no-header", action="store_true", help="Do not treat first row as header.")
    p.add_argument("--showindex", action="store_true", help="Show row index.")
    p.add_argument("file", nargs="?", help="Input file (default: stdin)")
    args = p.parse_args(argv)

    fmt = args.format
    if args.separator is not None:
        delim = args.separator
    else:
        if fmt == "csv":
            delim = ","
        elif fmt == "tsv":
            delim = "\t"
        else:
            delim = "\t"

    has_header = args.header and not args.no_header

    if args.file:
        with open(args.file, "r", newline="", encoding="utf-8") as fp:
            rows, hdr = _read_delimited(fp, delim, has_header)
    else:
        rows, hdr = _read_delimited(sys.stdin, delim, has_header)

    headers = hdr if hdr is not None else ()
    out = tabulate(rows, headers=headers, tablefmt=fmt, showindex=args.showindex)
    sys.stdout.write(out)
    if not out.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())