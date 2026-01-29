import argparse
import sys
from lib.core.data import cmdLineOptions

def cmdLineParser():
    parser = argparse.ArgumentParser(
        prog="sqlmap",
        description="Automatic SQL injection and database takeover tool",
        add_help=False,
        usage="python sqlmap.py [options]"
    )

    # Basic help
    parser.add_argument("-h", "--help", action="store_true", help="Show basic help message and exit")
    # Advanced help
    parser.add_argument("-hh", action="store_true", help="Show advanced help message and exit")
    # Version
    parser.add_argument("--version", action="store_true", help="Show program's version number and exit")

    # Example of a target option (not used in help tests)
    parser.add_argument("-u", "--url", metavar="URL", help="Target URL (e.g. 'http://www.site.com/vuln.php?id=1')")

    # Parse known args so we can handle -h/-hh/--version before erroring on unknowns
    args, unknown = parser.parse_known_args()

    # Handle help/version
    if args.help:
        parser.print_help()
        sys.exit(0)
    if args.hh:
        print("sqlmap advanced help:\n")
        parser.print_help()
        print("\nAdvanced options:\n  --batch         Never ask for user input, use default behaviour\n  --random-agent  Use a random User-Agent header\n  --proxy         Use a proxy to connect to the target URL")
        sys.exit(0)
    if args.version:
        from lib.core.settings import VERSION
        print(f"sqlmap version: {VERSION}")
        sys.exit(0)

    # If unknown arguments, print error and help
    if unknown:
        print(f"[ERROR] unknown option(s): {' '.join(unknown)}\n")
        parser.print_help()
        sys.exit(2)

    # Save parsed options to shared state
    for k, v in vars(args).items():
        setattr(cmdLineOptions, k, v)