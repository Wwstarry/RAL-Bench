import sys
import argparse
from .core import tabulate

def main():
    parser = argparse.ArgumentParser(description="Format tabular data as tables.")
    parser.add_argument("file", nargs="?", type=argparse.FileType("r"), default=sys.stdin,
                        help="Input file (default: stdin)")
    parser.add_argument("-f", "--format", default="plain",
                        choices=["plain", "grid", "pipe", "html", "tsv", "csv"],
                        help="Table format")
    parser.add_argument("-H", "--headers", nargs="+",
                        help="Headers for the table")
    parser.add_argument("-a", "--align", nargs="+",
                        choices=["left", "right", "center"],
                        help="Column alignments")
    args = parser.parse_args()

    # Read input lines
    lines = [line.rstrip("\n") for line in args.file]

    # Parse input as CSV or TSV or simple whitespace separated
    # We'll try to detect separator by format
    sep = None
    if args.format == "tsv":
        sep = "\t"
    elif args.format == "csv":
        sep = ","
    else:
        sep = None

    data = []
    if sep:
        import csv
        reader = csv.reader(lines, delimiter=sep)
        for row in reader:
            data.append(row)
    else:
        # whitespace split
        for line in lines:
            if line.strip() == "":
                continue
            data.append(line.split())

    # If headers given, use them, else try to guess
    headers = args.headers
    if headers is None and len(data) > 0:
        # Heuristic: if first row contains non-numeric strings, treat as header
        first = data[0]
        if any(not _is_number(cell) for cell in first):
            headers = first
            data = data[1:]

    # Alignments
    colalign = args.align

    output = tabulate(data, headers=headers, tablefmt=args.format, colalign=colalign)
    print(output)

def _is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

if __name__ == "__main__":
    main()