"""
Command-line interface for tabulate
"""

import sys
import argparse
from tabulate import tabulate


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Pretty-print tabular data"
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="Input file (default: stdin)"
    )
    parser.add_argument(
        "-f", "--format",
        default="simple",
        help="Table format (default: simple)"
    )
    parser.add_argument(
        "-s", "--sep",
        default=None,
        help="Column separator for input"
    )
    parser.add_argument(
        "-H", "--header",
        action="store_true",
        help="First row is header"
    )
    parser.add_argument(
        "-1", "--oneline",
        action="store_true",
        help="One record per line"
    )
    
    args = parser.parse_args()
    
    # Read input
    lines = args.file.readlines()
    
    if not lines:
        return
    
    # Parse data
    separator = args.sep if args.sep else None
    rows = []
    
    for line in lines:
        line = line.rstrip("\n\r")
        if separator:
            row = line.split(separator)
        else:
            # Auto-detect separator (tab or whitespace)
            if "\t" in line:
                row = line.split("\t")
            else:
                row = line.split()
        rows.append(row)
    
    # Handle headers
    headers = ()
    if args.header and rows:
        headers = rows[0]
        rows = rows[1:]
    
    # Format and print
    output = tabulate(rows, headers=headers, tablefmt=args.format)
    print(output)


if __name__ == "__main__":
    main()