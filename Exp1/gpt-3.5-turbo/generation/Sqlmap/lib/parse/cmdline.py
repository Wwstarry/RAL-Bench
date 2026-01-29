import argparse
import sys


class CustomHelpFormatter(argparse.RawTextHelpFormatter):
    def _format_action(self, action):
        # Override to add advanced help on -hh
        return super()._format_action(action)


def cmdLineParser():
    description = "sqlmap - automatic SQL injection and database takeover tool (pure python minimal)"
    epilog = "Use -hh for advanced help."

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False,
    )

    # Add help options
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show basic help message and exit",
    )
    parser.add_argument(
        "-hh",
        "--advanced-help",
        action="store_true",
        help="Show advanced help message and exit",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show program's version number and exit",
    )

    # Add some dummy options to simulate real sqlmap options
    parser.add_argument(
        "-u",
        "--url",
        help="Target URL",
        metavar="URL",
        default=None,
    )
    parser.add_argument(
        "-p",
        "--param",
        help="Parameter to test for SQL injection",
        metavar="PARAM",
        default=None,
    )
    parser.add_argument(
        "--level",
        type=int,
        choices=range(1, 6),
        default=1,
        help="Level of tests to perform (1-5) (default: 1)",
    )
    parser.add_argument(
        "--risk",
        type=int,
        choices=range(1, 4),
        default=1,
        help="Risk of tests to perform (1-3) (default: 1)",
    )

    # Parse known args first to handle -hh
    args, unknown = parser.parse_known_args()

    if getattr(args, "advanced_help", False):
        # Print advanced help and exit
        advanced_help_text = """
sqlmap advanced help:

Usage:
  python sqlmap.py [options]

Options:
  -h, --help            Show basic help message and exit
  -hh, --advanced-help  Show this advanced help message and exit
  --version             Show program's version number and exit

Target options:
  -u URL, --url=URL     Target URL to test for SQL injection
  -p PARAM, --param=PARAM
                        Parameter to test for SQL injection

Test options:
  --level LEVEL         Level of tests to perform (1-5)
  --risk RISK           Risk of tests to perform (1-3)

Examples:
  python sqlmap.py -u "http://testphp.vulnweb.com/artists.php?artist=1"
  python sqlmap.py -u "http://testphp.vulnweb.com/artists.php?artist=1" -p artist --level 3 --risk 2

For more information, visit: https://github.com/sqlmapproject/sqlmap
"""
        print(advanced_help_text.strip())
        sys.exit(0)

    return parser