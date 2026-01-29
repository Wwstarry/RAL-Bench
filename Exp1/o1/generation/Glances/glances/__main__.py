import sys
import argparse

from glances.stats import FIELD_FUNCTIONS
from glances import __version__

def main():
    parser = argparse.ArgumentParser(prog="glances", add_help=False)
    parser.add_argument("--help", action="store_true", default=False)
    parser.add_argument("-V", "--version", action="store_true", default=False)
    parser.add_argument("--stdout-csv", default=None, help="Output CSV for one shot and exit")

    args, extra = parser.parse_known_args()

    if args.help:
        print("Usage: glances [OPTIONS]")
        print("Options:")
        print("  --help             Show this message and exit")
        print("  -V, --version      Show version")
        print("  --stdout-csv FIELDS  Output CSV for one shot and exit")
        sys.exit(0)

    if args.version:
        print(__version__)
        sys.exit(0)

    if args.stdout_csv is None:
        print("Error: Missing required argument --stdout-csv", file=sys.stderr)
        sys.exit(1)

    fields_str = args.stdout_csv.strip()
    if not fields_str:
        print("Error: --stdout-csv expects a non-empty field list", file=sys.stderr)
        sys.exit(1)

    fields = fields_str.split(",")
    values = []

    for field in fields:
        if field not in FIELD_FUNCTIONS:
            print(f"Error: Unknown field '{field}'", file=sys.stderr)
            sys.exit(1)
        val = FIELD_FUNCTIONS[field]()
        values.append(str(val))

    print(",".join(values))
    sys.exit(0)

if __name__ == "__main__":
    main()