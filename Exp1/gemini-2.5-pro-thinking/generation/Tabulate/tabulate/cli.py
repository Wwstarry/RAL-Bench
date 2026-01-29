import argparse
import sys
from .core import tabulate
from .formats import _table_formats

def main():
    """Command-line interface for tabulate."""
    parser = argparse.ArgumentParser(
        description="Create a nicely formatted table from data.",
        prog="tabulate"
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="File to read data from (default: stdin)",
    )
    parser.add_argument(
        "-f",
        "--format",
        default="simple",
        help=f"Table format. Supported formats: {', '.join(sorted(_table_formats.keys()))}",
    )
    parser.add_argument(
        "-1", "--header", dest="header", action="store_true", help="First row of data is a header"
    )
    parser.add_argument(
        "-s", "--separator", default=None, help="Column separator (default: whitespace)"
    )
    parser.add_argument(
        "--numalign", default="decimal", help="Alignment for numbers (default: decimal)"
    )
    parser.add_argument(
        "--stralign", default="left", help="Alignment for strings (default: left)"
    )

    args = parser.parse_args()

    try:
        lines = args.file.readlines()
        
        if args.separator:
            data = [[cell.strip() for cell in line.strip().split(args.separator)] for line in lines if line.strip()]
        else:
            data = [line.strip().split() for line in lines if line.strip()]

        headers = []
        if args.header and data:
            headers = data.pop(0)

        output = tabulate(
            data,
            headers=headers,
            tablefmt=args.format,
            numalign=args.numalign,
            stralign=args.stralign,
        )
        print(output)
    except (ValueError, IndexError) as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(1)

if __name__ == "__main__":
    main()