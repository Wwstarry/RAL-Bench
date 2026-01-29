"""
Command-line parser for the stub sqlmap-like tool.

Exposes:
- cmdLineParser(args=None): parse CLI args, handle help/version, and return a namespace
"""

import argparse
import sys

from lib.core.data import cmdLineOptions
from lib.core.settings import VERSION, DESCRIPTION


BASIC_USAGE = "Usage: python sqlmap.py [options]"
BANNER = f"sqlmap/{VERSION}"


def _print_basic_help(parser: argparse.ArgumentParser) -> None:
    """
    Print basic help and usage.
    """
    sys.stdout.write(f"{BANNER}\n")
    # Use parser-generated help for consistency
    sys.stdout.write(parser.format_help())


def _print_advanced_help(parser: argparse.ArgumentParser) -> None:
    """
    Print advanced help with extra guidance and option list.
    """
    sys.stdout.write(f"{BANNER}\n")
    sys.stdout.write(f"{DESCRIPTION}\n\n")
    sys.stdout.write("Advanced help:\n")
    # Show the full parser help (includes all options)
    sys.stdout.write(parser.format_help())
    sys.stdout.write(
        "\nAdditional notes:\n"
        "- -hh prints this advanced help message\n"
        "- --version prints the application version\n"
        "- Typical target options include -u for URL and -r for request file\n"
    )


def cmdLineParser(args=None):
    """
    Parse command-line options and handle help/version output.

    If -h or -hh or --version are supplied, this function prints the appropriate
    output and exits the process. Otherwise it returns the parsed namespace and
    assigns it to lib.core.data.cmdLineOptions.
    """
    parser = argparse.ArgumentParser(
        prog="sqlmap.py",
        description=DESCRIPTION,
        add_help=True,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Custom advanced help flag
    parser.add_argument(
        "-hh", dest="advancedHelp", action="store_true",
        help="Show advanced help message and exit"
    )

    # Version flag
    parser.add_argument(
        "--version", dest="version", action="store_true",
        help="Show program's version number and exit"
    )

    # Target options (common in sqlmap)
    target = parser.add_argument_group("Target")
    target.add_argument("-u", "--url", dest="url", metavar="URL", help="Target URL (e.g. 'http://www.site.com/vuln.php?id=1')")
    target.add_argument("-d", "--data", dest="data", metavar="DATA", help="Data string to be sent through POST")
    target.add_argument("-r", dest="requestFile", metavar="FILE", help="Load HTTP request from a file")
    target.add_argument("-m", dest="bulkFile", metavar="FILE", help="Load multiple targets from a file")
    target.add_argument("-l", dest="logFile", metavar="FILE", help="Parse targets from Burp or WebScarab proxy logs")
    target.add_argument("-c", dest="configFile", metavar="FILE", help="Load options from a configuration INI file")
    target.add_argument("-g", dest="googleDork", metavar="DORK", help="Process Google dork results")
    target.add_argument("-t", dest="threads", metavar="NUM", type=int, default=1, help="Maximum number of concurrent HTTP requests")

    # General options (subset)
    general = parser.add_argument_group("General")
    general.add_argument("--random-agent", dest="randomAgent", action="store_true", help="Use randomly selected HTTP User-Agent header")
    general.add_argument("--batch", dest="batch", action="store_true", help="Never ask for user input, use defaults")
    general.add_argument("--disable-coloring", dest="disableColoring", action="store_true", help="Disable console coloring")

    # Parse arguments
    try:
        namespace = parser.parse_args(args=args)
    except SystemExit:
        # argparse already printed error/help and exited; re-raise to maintain behavior
        raise

    # Handle special flags
    if getattr(namespace, "version", False):
        sys.stdout.write(f"{BANNER}\n")
        sys.exit(0)

    if getattr(namespace, "advancedHelp", False):
        _print_advanced_help(parser)
        sys.exit(0)

    # Store parsed options to global state
    global cmdLineOptions
    cmdLineOptions = namespace
    return namespace