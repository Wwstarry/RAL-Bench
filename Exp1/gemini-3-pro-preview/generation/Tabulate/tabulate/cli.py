import sys
import argparse
from .core import tabulate
from .formats import tabulate_formats

def main():
    parser = argparse.ArgumentParser(description="Pretty-print tabular data")
    parser.add_argument("file", nargs="?", type=argparse.FileType("r"), default=sys.stdin,
                        help="Input file (default: stdin)")
    parser.add_argument("--header", action="store_true", help="First row is header")
    parser.add_argument("-f", "--format", default="simple", choices=tabulate_formats,
                        help="Output format")
    parser.add_argument("-s", "--sep", default=None, help="Input separator (default: whitespace)")
    
    args = parser.parse_args()

    # Basic CSV/TSV parsing logic for CLI
    lines = args.file.readlines()
    data = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if args.sep:
            row = line.split(args.sep)
        else:
            row = line.split()
        data.append(row)

    if not data:
        return

    headers = "firstrow" if args.header else ()
    
    # If header flag is not set, but we want to treat first row as data, 
    # tabulate handles headers=() by default.
    
    print(tabulate(data, headers=headers, tablefmt=args.format))

if __name__ == "__main__":
    main()