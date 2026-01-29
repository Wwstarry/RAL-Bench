import sys
import argparse
from . import __version__
from .monitor import get_metrics


def parse_args():
    parser = argparse.ArgumentParser(
        description="Glances-compatible system monitoring tool",
        add_help=False,
    )
    parser.add_argument(
        "-V", "--version",
        action="store_true",
        help="Print version and exit"
    )
    parser.add_argument(
        "--stdout-csv",
        metavar="FIELDS",
        help="Output one-shot CSV line with specified fields and exit"
    )
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show this help message and exit"
    )
    args, unknown = parser.parse_known_args()
    # If unknown args exist and not --stdout-csv, treat as error
    if unknown:
        # But allow unknown only if --stdout-csv is present? No, spec says predictable for invalid invocations.
        # So unknown args cause error.
        print(f"Unknown arguments: {' '.join(unknown)}", file=sys.stderr)
        sys.exit(1)
    return args


def print_help():
    help_text = """usage: python -m glances [options]

Options:
  -h, --help            Show this help message and exit
  -V, --version         Print version and exit
  --stdout-csv FIELDS   Output one-shot CSV line with specified fields and exit

FIELDS is a comma-separated list of fields. Supported fields:
  now
  cpu.user
  cpu.total
  mem.used
  load
"""
    print(help_text)


def main():
    args = parse_args()

    if args.help:
        print_help()
        sys.exit(0)

    if args.version:
        print(__version__)
        sys.exit(0)

    if args.stdout_csv is None:
        # Missing --stdout-csv argument must exit non-zero
        print("error: missing --stdout-csv argument", file=sys.stderr)
        sys.exit(1)

    fields = [f.strip() for f in args.stdout_csv.split(",") if f.strip()]
    if not fields:
        print("error: --stdout-csv requires at least one field", file=sys.stderr)
        sys.exit(1)

    # Validate fields
    valid_fields = {"now", "cpu.user", "cpu.total", "mem.used", "load"}
    for f in fields:
        if f not in valid_fields:
            print(f"error: unknown field '{f}'", file=sys.stderr)
            sys.exit(1)

    metrics = get_metrics()

    # Compose output line
    output_values = []
    for f in fields:
        if f == "now":
            output_values.append(metrics["now"])
        elif f == "cpu.user":
            output_values.append(f"{metrics['cpu.user']:.2f}")
        elif f == "cpu.total":
            output_values.append(f"{metrics['cpu.total']:.2f}")
        elif f == "mem.used":
            output_values.append(str(metrics["mem.used"]))
        elif f == "load":
            output_values.append(f"{metrics['load']:.2f}")
        else:
            # Should never happen due to validation above
            output_values.append("")

    print(",".join(output_values))
    sys.exit(0)


if __name__ == "__main__":
    main()