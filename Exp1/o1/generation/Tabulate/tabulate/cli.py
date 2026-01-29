"""
A simple command-line interface for this tabulate module.
Reads lines from stdin, splits into columns, and prints using a chosen format.
Usage:
    python -m tabulate.cli [--tablefmt=FORMAT]
"""

import sys
import argparse
from .core import tabulate

def main():
    parser = argparse.ArgumentParser(description="A simple tabulate CLI.")
    parser.add_argument(
        "--tablefmt",
        default="plain",
        help="Table format (plain, grid, pipe, html, csv, tsv, etc.)",
    )
    args = parser.parse_args()

    # read from stdin
    data = []
    for line in sys.stdin:
        line = line.strip("\n")
        # split by whitespace
        row = line.split()
        data.append(row)

    # generate output
    result = tabulate(data, headers=None, tablefmt=args.tablefmt)
    print(result)

if __name__ == "__main__":
    main()