"""
Main entry point for the glances CLI.

This module provides a command-line interface that is a subset of the
original Glances project, focusing on the one-shot CSV output feature.
"""
import argparse
import sys
import csv

from . import __version__
from .stats import get_all_stats_mappers

def run_csv_output(fields_str):
    """
    Collects stats for the requested fields and prints them as a single CSV line.
    """
    requested_fields = [f.strip() for f in fields_str.split(',') if f.strip()]

    try:
        mappers = get_all_stats_mappers()
    except Exception as e:
        sys.stderr.write(f"Error initializing stats collector: {e}\n")
        sys.exit(1)

    available_fields = mappers.keys()
    unknown_fields = set(requested_fields) - set(available_fields)

    if unknown_fields:
        sys.stderr.write(f"Error: Unknown field(s) provided: {', '.join(sorted(unknown_fields))}\n")
        sys.exit(1)

    try:
        values = [mappers[field]() for field in requested_fields]
    except Exception as e:
        sys.stderr.write(f"Error collecting stats: {e}\n")
        sys.exit(1)

    # Use the csv module to ensure proper formatting
    writer = csv.writer(sys.stdout)
    writer.writerow(values)
    sys.exit(0)

def main():
    """
    Parses command-line arguments and executes the requested action.
    """
    parser = argparse.ArgumentParser(
        description="A cross-platform system monitoring tool.",
        # Disable default help to customize its group and text
        add_help=False
    )

    # Group for standard options like help and version
    std_group = parser.add_argument_group('Standard Options')
    std_group.add_argument(
        '-h', '--help', action='help',
        help='show this help message and exit'
    )
    std_group.add_argument(
        '-V', '--version', action='version',
        version=f'Glances {__version__}',
        help="show program's version number and exit"
    )

    # Group for one-shot output modes
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--stdout-csv', dest='csv_fields',
        metavar='<FIELDS>',
        help='Print stats to stdout in CSV format (one-shot)'
    )

    args = parser.parse_args()

    if args.csv_fields:
        run_csv_output(args.csv_fields)
    else:
        # In this implementation, --stdout-csv is the only supported operational mode.
        # If it's not provided, we must exit with an error.
        parser.print_usage(sys.stderr)
        sys.stderr.write("glances: error: missing required argument for output mode (e.g., --stdout-csv)\n")
        sys.exit(1)

if __name__ == '__main__':
    main()