from __future__ import annotations

import argparse
import csv
import sys
from typing import List, Optional

from .core import tabulate
from .formats import tabulate_formats


def _read_delimited(stream, delimiter: str) -> List[List[str]]:
    reader = csv.reader(stream, delimiter=delimiter)
    return [row for row in reader]


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="tabulate", add_help=True)
    p.add_argument("--format", "-f", dest="tablefmt", default="simple", choices=sorted(tabulate_formats.keys()))
    p.add_argument("--headers", dest="headers", default="firstrow", help="Use 'firstrow', 'keys', or empty for none")
    p.add_argument("--delimiter", "-d", default=None, help="Input delimiter (default: auto/tab)")
    p.add_argument("--showindex", action="store_true", help="Add row index column")
    args = p.parse_args(argv)

    data_in = sys.stdin.read().splitlines()
    if not data_in:
        return 0

    # auto delimiter
    delim = args.delimiter
    if delim is None:
        delim = "\t" if any("\t" in ln for ln in data_in) else ","

    rows = _read_delimited(data_in, delim) if isinstance(data_in, list) else _read_delimited(sys.stdin, delim)

    headers = args.headers
    if headers == "" or headers.lower() in ("none", "no", "0"):
        headers = ()

    out = tabulate(rows, headers=headers, tablefmt=args.tablefmt, showindex=args.showindex)
    sys.stdout.write(out)
    if not out.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())