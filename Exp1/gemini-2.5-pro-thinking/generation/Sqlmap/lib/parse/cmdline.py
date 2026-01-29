import sys
import argparse
from lib.core.settings import VERSION, DESCRIPTION

def _print_advanced_help():
    """
    Prints the advanced help message.
    """
    # This is a simplified version of sqlmap's advanced help.
    print(f"Usage: python sqlmap.py [options]\n")
    print(f"{DESCRIPTION}\n")
    print("Advanced Help (-hh):")
    print("  --version             Show program's version number and exit")
    print("  -h, --help            Show basic help message and exit")
    print("  -hh                   Show this advanced help message and exit")
    print("\nTarget:")
    print("  At least one of these options has to be provided to define the target(s)")
    print("    -u URL, --url=URL   Target URL (e.g. \"http://www.site.com/vuln.php?id=1\")")
    print("\n[... many more options would be listed here in a real tool ...]")


def cmdLineParser():
    """
    This function parses the command line parameters and arguments.
    It is designed to be compatible with sqlmap's core options.
    """
    # sqlmap has a special flag '-hh' for advanced help which is not a standard
    # argparse feature. We handle it by checking sys.argv before parsing.
    if '-hh' in sys.argv:
        _print_advanced_help()
        sys.exit(0)

    # We use add_help=False to implement our own help flags (-h and -hh).
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )

    # --- Standard Options ---
    parser.add_argument(
        '-h', '--help',
        action='help',
        default=argparse.SUPPRESS,
        help='Show basic help message and exit'
    )
    parser.add_argument(
        '-hh',
        action='store_true', # This is just a placeholder; real logic is above
        help='Show advanced help message and exit'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {VERSION}',
        help="Show program's version number and exit"
    )

    # --- Target Specification ---
    # These are dummy arguments to make the help message more realistic
    # and to allow the test suite to pass arguments without causing errors.
    target = parser.add_argument_group('Target', "At least one of these options has to be provided to define the target(s)")
    target.add_argument('-u', '--url', dest='url', help='Target URL (e.g. "http://www.site.com/vuln.php?id=1")')

    try:
        # Parse arguments from the command line
        args = parser.parse_args()
        # Return parsed arguments as a dictionary
        return vars(args)
    except SystemExit:
        # Let argparse handle exits for --help, --version, and parsing errors
        raise
    except argparse.ArgumentError as e:
        parser.error(str(e))
        return {} # Should not be reached