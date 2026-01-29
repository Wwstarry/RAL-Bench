import sys
import argparse
from . import __version__
from .fields import FIELD_MAP, get_field_value

def print_version():
    print(f"glances {__version__}")

def print_help():
    print(
        "usage: glances [--help] [-V|--version] [--stdout-csv FIELDS]\n"
        "\n"
        "Options:\n"
        "  --help            Show this help message and exit\n"
        "  -V, --version     Show version and exit\n"
        "  --stdout-csv FIELDS\n"
        "                    Output one-shot CSV line for comma-separated field list\n"
        "\n"
        "Supported fields for --stdout-csv:\n"
        "  now, cpu.user, cpu.total, mem.used, load\n"
    )

def run_cli(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="glances",
        add_help=False,
        allow_abbrev=False,
        usage="glances [--help] [-V|--version] [--stdout-csv FIELDS]",
        description=None,
    )
    parser.add_argument("--help", action="store_true", dest="help")
    parser.add_argument("-V", "--version", action="store_true", dest="version")
    parser.add_argument("--stdout-csv", metavar="FIELDS", dest="stdout_csv", default=None)

    try:
        args, unknown = parser.parse_known_args(argv)
    except Exception as e:
        print(f"glances: {e}", file=sys.stderr)
        sys.exit(2)

    if args.help:
        print_help()
        sys.exit(0)

    if args.version:
        print_version()
        sys.exit(0)

    if args.stdout_csv is not None:
        # Only --stdout-csv is allowed with its argument
        fields = [f.strip() for f in args.stdout_csv.split(",") if f.strip()]
        if not fields:
            print("glances: --stdout-csv requires at least one field", file=sys.stderr)
            sys.exit(2)
        # Validate fields
        for f in fields:
            if f not in FIELD_MAP:
                print(f"glances: unknown field '{f}'", file=sys.stderr)
                sys.exit(2)
        # Output CSV header? The reference does not, so only values
        try:
            values = []
            for f in fields:
                v = get_field_value(f)
                # For now, print as float for numeric fields, as required
                values.append(str(v))
            print(",".join(values))
            sys.exit(0)
        except Exception as e:
            print(f"glances: error: {e}", file=sys.stderr)
            sys.exit(2)

    # If no recognized arguments, print help and exit non-zero
    print("glances: missing required argument", file=sys.stderr)
    print_help()
    sys.exit(2)