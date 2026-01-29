from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .core import tabulate


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="tabulate", add_help=True)
    parser.add_argument(
        "--format",
        dest="tablefmt",
        default="simple",
        help="Table format (e.g. simple, plain, grid, pipe, tsv, csv, html).",
    )
    parser.add_argument(
        "--headers",
        dest="headers",
        default="",
        help="Comma-separated headers. If omitted, no headers are used.",
    )
    parser.add_argument(
        "rows",
        nargs="*",
        help="Rows as comma-separated values; each argument is one row.",
    )

    ns = parser.parse_args(argv)

    headers = ()
    if ns.headers:
        headers = [h for h in ns.headers.split(",")]

    data = []
    for r in ns.rows:
        data.append([c for c in r.split(",")])

    out = tabulate(data, headers=headers, tablefmt=ns.tablefmt)
    sys.stdout.write(out)
    if out and not out.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())