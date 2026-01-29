import sys
import argparse
from glances import __version__
from glances.monitor import get_system_metrics

def parse_args():
    """
    Parse command-line arguments for the CLI.
    """
    parser = argparse.ArgumentParser(
        description="Glances-like system monitoring tool."
    )
    parser.add_argument(
        "-V", "--version",
        action="store_true",
        help="Print version information and exit."
    )
    parser.add_argument(
        "--stdout-csv",
        type=str,
        help="Output system metrics as a CSV line. Specify fields as a comma-separated list."
    )
    return parser.parse_args()

def validate_fields(fields):
    """
    Validate the requested fields against available metrics.
    """
    valid_fields = {"now", "cpu.user", "cpu.total", "mem.used", "load"}
    for field in fields:
        if field not in valid_fields:
            raise ValueError(f"Unknown field: {field}")

def main():
    args = parse_args()

    if args.version:
        print(f"Glances-like tool version {__version__}")
        sys.exit(0)

    if args.stdout_csv:
        fields = args.stdout_csv.split(",")
        try:
            validate_fields(fields)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        metrics = get_system_metrics()
        try:
            csv_output = ",".join(str(metrics[field]) for field in fields)
            print(csv_output)
            sys.exit(0)
        except KeyError:
            print("Error: Missing field in metrics.", file=sys.stderr)
            sys.exit(1)

    print("Error: Missing required argument --stdout-csv.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()