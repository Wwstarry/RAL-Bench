"""Command-line interface for Glances."""
import argparse
import sys
import time

from glances.monitor import SystemMonitor


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Glances - A cross-platform system monitoring tool",
        add_help=False
    )
    
    parser.add_argument(
        '-V', '--version',
        action='store_true',
        help='Show version and exit'
    )
    
    parser.add_argument(
        '--stdout-csv',
        metavar='FIELDS',
        help='Output one-shot CSV data with specified fields'
    )
    
    parser.add_argument(
        '-h', '--help',
        action='store_true',
        help='Show this help message and exit'
    )
    
    return parser.parse_args()


def validate_fields(fields):
    """Validate CSV field patterns."""
    valid_fields = {'now', 'cpu.user', 'cpu.total', 'mem.used', 'load'}
    
    for field in fields:
        if field not in valid_fields:
            return False, f"Unknown field: {field}"
    
    return True, None


def format_csv_value(monitor, field):
    """Format a single field value for CSV output."""
    if field == 'now':
        return str(time.time())
    elif field == 'cpu.user':
        return f"{monitor.get_cpu_user():.2f}"
    elif field == 'cpu.total':
        return f"{monitor.get_cpu_total():.2f}"
    elif field == 'mem.used':
        return str(monitor.get_mem_used())
    elif field == 'load':
        return f"{monitor.get_load():.2f}"
    else:
        return "0"


def main():
    """Main CLI entry point."""
    args = parse_args()
    
    # Handle help
    if args.help:
        print("""Glances - A cross-platform system monitoring tool

Usage: python -m glances [OPTIONS]

Options:
  -V, --version           Show version and exit
  --stdout-csv FIELDS     Output one-shot CSV data with specified fields
  -h, --help             Show this help message and exit

Supported CSV fields: now, cpu.user, cpu.total, mem.used, load""")
        return 0
    
    # Handle version
    if args.version:
        from glances import __version__
        print(f"Glances {__version__}")
        return 0
    
    # Handle CSV output
    if args.stdout_csv is not None:
        if not args.stdout_csv.strip():
            print("Error: Missing fields for --stdout-csv", file=sys.stderr)
            return 1
        
        fields = [f.strip() for f in args.stdout_csv.split(',')]
        is_valid, error_msg = validate_fields(fields)
        
        if not is_valid:
            print(f"Error: {error_msg}", file=sys.stderr)
            return 1
        
        monitor = SystemMonitor()
        values = [format_csv_value(monitor, field) for field in fields]
        print(','.join(values))
        return 0
    
    # Default behavior (no arguments)
    print("Error: No mode specified. Use --help for usage information.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())