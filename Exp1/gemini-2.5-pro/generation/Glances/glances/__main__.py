# glances/__main__.py

import argparse
import sys
import csv

from . import __version__
from .stats import GlancesStats

def main():
    """Main function for the Glances CLI."""
    parser = argparse.ArgumentParser(
        description="A cross-platform system monitoring tool, API-compatible with Glances.",
        epilog="This tool provides a subset of Glances' functionality for one-shot monitoring.",
        add_help=True
    )

    parser.add_argument(
        '-V', '--version',
        action='version',
        version=f'Glances {__version__}'
    )

    parser.add_argument(
        '--stdout-csv',
        dest='csv_fields',
        metavar='FIELDS',
        help='Print stats to stdout in CSV format (one-shot mode). '
             'FIELDS is a comma-separated list of stat fields.'
    )

    args = parser.parse_args()

    if args.csv_fields:
        # Strip whitespace and filter out any empty strings that might result
        # from trailing commas or multiple commas.
        fields = [f.strip() for f in args.csv_fields.split(',') if f.strip()]

        if not fields:
            print("Error: No fields provided for --stdout-csv.", file=sys.stderr)
            sys.exit(1)

        try:
            stats_collector = GlancesStats()
            values = [stats_collector.get_value(field) for field in fields]
        except KeyError as e:
            # The error message from GlancesStats is already informative.
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            # Catch other potential psutil errors
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
            sys.exit(1)

        # Use the csv module to ensure correct formatting.
        # lineterminator='\n' is important for cross-platform consistency.
        writer = csv.writer(sys.stdout, lineterminator='\n')
        writer.writerow(values)
        sys.exit(0)
    else:
        # This block is reached if --stdout-csv is not provided.
        # Since it's the only operational argument, this is an error.
        parser.print_usage(file=sys.stderr)
        print("\nError: Missing required argument --stdout-csv", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()