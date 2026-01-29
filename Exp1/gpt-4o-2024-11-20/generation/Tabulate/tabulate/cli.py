# tabulate/cli.py

import sys
import argparse
from .core import tabulate

def main():
    parser = argparse.ArgumentParser(description="Format tabular data.")
    parser.add_argument("input", type=str, help="Input data file (JSON or CSV).")
    parser.add_argument("--headers", type=str, nargs="*", help="Column headers.")
    parser.add_argument("--format", type=str, default="plain", help="Table format.")
    parser.add_argument("--numalign", type=str, default="right", help="Numeric column alignment.")
    parser.add_argument("--stralign", type=str, default="left", help="String column alignment.")
    args = parser.parse_args()

    try:
        with open(args.input, "r") as f:
            data = eval(f.read())  # Simplified for demonstration; use json/csv parsing in production.
        headers = args.headers
        table = tabulate(data, headers=headers, tablefmt=args.format, numalign=args.numalign, stralign=args.stralign)
        print(table)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()