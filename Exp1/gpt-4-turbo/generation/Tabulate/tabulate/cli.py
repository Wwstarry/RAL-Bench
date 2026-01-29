import sys
from .core import tabulate

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Format tabular data.")
    parser.add_argument("-f", "--format", default="simple", help="Table format")
    parser.add_argument("-H", "--headers", default="", help="Headers (comma separated or 'keys'/'firstrow')")
    parser.add_argument("-d", "--delimiter", default=None, help="Input delimiter (default: auto)")
    parser.add_argument("-i", "--showindex", action="store_true", help="Show row index")
    parser.add_argument("file", nargs="?", default=None, help="Input file (default: stdin)")
    args = parser.parse_args()

    # Read input
    if args.file and args.file != "-":
        with open(args.file) as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()

    # Parse input as CSV/TSV or whitespace
    if args.delimiter:
        delimiter = args.delimiter
    else:
        # Guess delimiter
        if lines and "\t" in lines[0]:
            delimiter = "\t"
        elif lines and "," in lines[0]:
            delimiter = ","
        else:
            delimiter = None

    if delimiter:
        import csv
        reader = csv.reader(lines, delimiter=delimiter)
        data = [row for row in reader]
    else:
        data = [line.strip().split() for line in lines if line.strip()]

    # Headers
    if args.headers == "keys":
        headers = "keys"
    elif args.headers == "firstrow":
        headers = "firstrow"
    elif args.headers:
        headers = [h.strip() for h in args.headers.split(",")]
    else:
        headers = ()

    print(tabulate(data, headers=headers, tablefmt=args.format, showindex=args.showindex))

if __name__ == "__main__":
    main()