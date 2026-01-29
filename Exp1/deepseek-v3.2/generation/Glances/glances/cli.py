"""
Command-line interface for Glances
"""

import sys
import argparse
from typing import List, Optional
from glances.core import Glances


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Glances - A cross-platform system monitoring tool",
        add_help=False
    )
    
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show this help message and exit"
    )
    
    parser.add_argument(
        "-V", "--version",
        action="store_true",
        help="Show version information and exit"
    )
    
    parser.add_argument(
        "--stdout-csv",
        metavar="FIELDS",
        help="Output one-shot CSV with specified fields"
    )
    
    return parser.parse_args(args)


def print_help() -> None:
    """Print help message"""
    help_text = """usage: python -m glances [-h] [-V] [--stdout-csv FIELDS]

Glances - A cross-platform system monitoring tool

optional arguments:
  -h, --help           Show this help message and exit
  -V, --version        Show version information and exit
  --stdout-csv FIELDS  Output one-shot CSV with specified fields

Supported CSV fields:
  now        Current timestamp
  cpu.user   CPU user percentage
  cpu.total  CPU total percentage
  mem.used   Memory used percentage
  load       System load average (1-minute)
"""
    print(help_text)


def print_version() -> None:
    """Print version information"""
    from glances import __version__
    print(f"Glances {__version__}")


def validate_csv_fields(fields_str: str) -> List[str]:
    """Validate CSV fields and return list of valid fields"""
    if not fields_str:
        raise ValueError("No fields specified")
    
    fields = [f.strip() for f in fields_str.split(",")]
    valid_fields = {"now", "cpu.user", "cpu.total", "mem.used", "load"}
    
    for field in fields:
        if field not in valid_fields:
            raise ValueError(f"Unknown field: {field}")
    
    return fields


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point"""
    parsed_args = parse_args(args)
    
    # Handle help flag
    if parsed_args.help:
        print_help()
        return 0
    
    # Handle version flag
    if parsed_args.version:
        print_version()
        return 0
    
    # Handle CSV output
    if parsed_args.stdout_csv is not None:
        try:
            fields = validate_csv_fields(parsed_args.stdout_csv)
            glances = Glances()
            csv_row = glances.get_csv_row(fields)
            print(csv_row)
            return 0
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 1
    
    # No valid command specified
    print("Error: No valid command specified. Use --help for usage.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())