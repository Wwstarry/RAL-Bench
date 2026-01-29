import argparse
import sys
from .version import __version__
from .stats import get_stats
from .formatter import format_csv

def main():
    parser = argparse.ArgumentParser(description='Glances - Cross-platform system monitoring tool')
    parser.add_argument('-V', '--version', action='store_true', help='Show version and exit')
    parser.add_argument('--stdout-csv', metavar='FIELDS', type=str, help='Output stats as CSV to stdout (comma separated list of fields)')
    
    args = parser.parse_args()
    
    if args.version:
        print(f"Glances v{__version__}")
        sys.exit(0)
    
    if args.stdout_csv is not None:
        fields = args.stdout_csv.split(',')
        stats = get_stats()
        try:
            csv_output = format_csv(stats, fields)
            print(csv_output)
            sys.exit(0)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif '--stdout-csv' in sys.argv:
        print("Error: Missing argument for --stdout-csv", file=sys.stderr)
        sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)

if __name__ == "__main__":
    main()