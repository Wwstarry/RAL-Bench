from __future__ import annotations

import argparse
import sys

from lib.core.settings import VERSION, DESCRIPTION


class _AdvancedHelpAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # Print basic help first, then an advanced section.
        parser.print_help(sys.stdout)
        sys.stdout.write("\n")
        sys.stdout.write("Advanced help (stub)\n")
        sys.stdout.write("====================\n")
        sys.stdout.write(
            "This is a lightweight, interface-compatible stub of sqlmap.\n"
            "It supports CLI parsing and benign execution without performing\n"
            "any network requests or SQL injection testing.\n\n"
        )
        sys.stdout.write("Common options:\n")
        sys.stdout.write("  -u, --url URL           Target URL (no network calls will be made)\n")
        sys.stdout.write("  --data DATA             Data string to be sent through POST\n")
        sys.stdout.write("  -p PARAM                Testable parameter(s)\n")
        sys.stdout.write("  --batch                 Never ask for user input\n")
        sys.stdout.write("  -v VERBOSE              Verbosity level (0-6)\n")
        sys.stdout.write("  --risk RISK             Risk of tests to perform (1-3)\n")
        sys.stdout.write("  --level LEVEL           Level of tests to perform (1-5)\n")
        sys.stdout.write("  --random-agent          Use a random HTTP User-Agent header\n")
        sys.stdout.write("  --threads THREADS       Max number of concurrent threads\n")
        sys.stdout.write("  --tamper TAMPER         Tamper scripts (comma-separated)\n\n")
        sys.stdout.write("Examples:\n")
        sys.stdout.write("  python sqlmap.py -u http://example.com/page?id=1 --batch\n")
        sys.stdout.write("  python sqlmap.py -u http://example.com/login --data \"u=a&p=b\" -p u\n")
        raise SystemExit(0)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlmap.py",
        description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=True,
    )

    # Special flags expected by tests
    parser.add_argument(
        "-hh",
        dest="advanced_help",
        nargs=0,
        action=_AdvancedHelpAction,
        help="Show advanced help message and exit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"sqlmap/{VERSION}",
        help="Show program's version number and exit",
    )

    # Minimal set of common sqlmap-ish options (no-ops for this stub)
    parser.add_argument("-u", "--url", dest="url", help="Target URL")
    parser.add_argument("--data", dest="data", help="Data string to be sent through POST")
    parser.add_argument("-p", dest="param", help="Testable parameter(s)")
    parser.add_argument("--batch", dest="batch", action="store_true", help="Never ask for user input")
    parser.add_argument("-v", dest="verbose", type=int, default=0, help="Verbosity level (0-6)")
    parser.add_argument("--risk", dest="risk", type=int, default=1, help="Risk of tests to perform (1-3)")
    parser.add_argument("--level", dest="level", type=int, default=1, help="Level of tests to perform (1-5)")
    parser.add_argument("--random-agent", dest="random_agent", action="store_true", help="Use a random User-Agent")
    parser.add_argument("--threads", dest="threads", type=int, default=1, help="Max number of threads")
    parser.add_argument("--tamper", dest="tamper", help="Tamper scripts (comma-separated)")

    return parser


def cmdLineParser(argv=None, build_only: bool = False):
    """
    Parse command line arguments.

    If build_only=True, returns the ArgumentParser instance without parsing.
    """
    parser = _build_parser()
    if build_only:
        return parser
    return parser.parse_args(args=argv)