"""
Command-line interface for tabulate.
"""

import sys
import argparse
from tabulate import tabulate, list_formats


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Format tabular data as a table"
    )
    parser.add_argument(
        "input",
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
        "--list-formats",
        action="store_true",
        help="List available formats"
    )
    parser.add_argument(
        "-d", "--delimiter",
        default=None,
        help="Delimiter for input data"
    )
    parser.add_argument(
        "--headers",
        default="",
        help="Column headers (comma-separated)"
    )
    
    args = parser.parse_args()
    
    if args.list_formats:
        for fmt in list_formats():
            print(fmt)
        return
    
    # Read input
    content = args.input.read()
    
    # Parse input
    lines = content.strip().split("\n")
    if not lines:
        return
    
    # Simple CSV parsing
    if args.delimiter:
        rows = [line.split(args.delimiter) for line in lines]
    else:
        rows = [line.split() for line in lines]
    
    # Parse headers
    headers = []
    if args.headers:
        headers = args.headers.split(",")
    
    # Format table
    result = tabulate(rows, headers=headers, tablefmt=args.format)
    print(result)


if __name__ == "__main__":
    main()