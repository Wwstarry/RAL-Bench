import argparse
import sys
from typing import Optional, Sequence

from .core import tabulate

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Pretty-print tabular data")
    parser.add_argument(
        "-H", "--headers", action="store_true", help="use first row as headers"
    )
    parser.add_argument(
        "-s", "--sep", default=" ", help="field separator (default: ' ')"
    )
    parser.add_argument(
        "-f",
        "--format",
        default="plain",
        help="output format (default: plain)",
    )
    parser.add_argument(
        "-i", "--index", action="store_true", help="show row indices"
    )
    parser.add_argument("file", nargs="?", help="input file (default: stdin)")

    args = parser.parse_args(argv)

    if args.file:
        with open(args.file) as f:
            data = [line.strip().split(args.sep) for line in f]
    else:
        data = [line.strip().split(args.sep) for line in sys.stdin]

    headers = "firstrow" if args.headers else ()
    print(tabulate(data, headers=headers, tablefmt=args.format, showindex=args.index))

    return 0

if __name__ == "__main__":
    sys.exit(main())