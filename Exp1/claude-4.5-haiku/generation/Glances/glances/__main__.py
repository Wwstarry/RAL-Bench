"""Command-line interface for Glances."""

import sys
import argparse
from glances import __version__
from glances.core import GlancesCore


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="glances",
        description="A cross-platform system monitoring tool",
    )
    
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    
    parser.add_argument(
        "--stdout-csv",
        metavar="FIELDS",
        help="Output CSV data for specified fields and exit",
    )
    
    args = parser.parse_args()
    
    if args.stdout_csv is not None:
        try:
            fields = [f.strip() for f in args.stdout_csv.split(",")]
            
            # Validate fields before processing
            valid_fields = {
                "now", "cpu.user", "cpu.total", "cpu.percent",
                "mem.used", "mem.total", "mem.percent", "load"
            }
            
            for field in fields:
                if field not in valid_fields:
                    sys.stderr.write(f"Error: Unknown field '{field}'\n")
                    sys.exit(1)
            
            core = GlancesCore()
            csv_line = core.get_csv_line(fields)
            print(csv_line)
            sys.exit(0)
        except ValueError as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.exit(1)
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.exit(1)


if __name__ == "__main__":
    main()