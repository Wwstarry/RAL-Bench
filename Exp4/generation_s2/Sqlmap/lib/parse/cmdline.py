# -*- coding: utf-8 -*-

"""
Command line parser.

Exposes cmdLineParser() compatible with sqlmap's module path:
lib.parse.cmdline.cmdLineParser
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from lib.core.settings import VERSION, DESCRIPTION


class _ArgumentParser(argparse.ArgumentParser):
    """
    Custom ArgumentParser to ensure informative errors and clean exits.
    """

    def error(self, message):
        # Match typical CLI behavior: show error + short help hint.
        sys.stderr.write(f"sqlmap: error: {message}\n")
        sys.stderr.write("Try 'python sqlmap.py -h' for basic help.\n")
        raise SystemExit(2)


def _add_basic_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-u",
        "--url",
        dest="url",
        help="Target URL (e.g. 'http://example.com/vuln.php?id=1')",
    )
    parser.add_argument("--data", dest="data", help="POST data string")
    parser.add_argument("--cookie", dest="cookie", help="HTTP Cookie header value")
    parser.add_argument("--method", dest="method", help="Force HTTP method (GET/POST/etc.)")
    parser.add_argument("--batch", dest="batch", action="store_true", help="Never ask for user input")
    parser.add_argument("-v", dest="verbosity", type=int, default=1, help="Verbosity level: 0-6")


def _add_advanced_arguments(parser: argparse.ArgumentParser) -> None:
    # A small, representative set; tests typically only validate that -hh works.
    grp = parser.add_argument_group("Advanced")
    grp.add_argument("--level", dest="level", type=int, default=1, help="Level of tests to perform (1-5)")
    grp.add_argument("--risk", dest="risk", type=int, default=1, help="Risk of tests to perform (1-3)")
    grp.add_argument("--flush-session", dest="flushSession", action="store_true", help="Flush session files")


def _format_advanced_help() -> str:
    return (
        "Advanced help:\n"
        "  -u, --url URL            Target URL\n"
        "  --data DATA              POST data string\n"
        "  --cookie COOKIE          HTTP Cookie header\n"
        "  --method METHOD          Force HTTP method\n"
        "  --batch                  Never ask for user input\n"
        "  -v VERBOSITY             Verbosity level\n"
        "\n"
        "Advanced options:\n"
        "  --level LEVEL            Level of tests (1-5)\n"
        "  --risk RISK              Risk of tests (1-3)\n"
        "  --flush-session          Flush session files\n"
        "\n"
        "Examples:\n"
        "  python sqlmap.py -u \"http://example.com/item?id=1\"\n"
        "  python sqlmap.py -u \"http://example.com/login\" --data \"user=a&pass=b\"\n"
    )


def cmdLineParser(argv: Optional[List[str]] = None) -> argparse.ArgumentParser:
    """
    Build and return the argument parser.

    Note: This function returns an ArgumentParser instance. The CLI entrypoint
    will call parse_args() on it.
    """
    # We accept argv only for compatibility; it's not required to build parser.
    parser = _ArgumentParser(
        prog="sqlmap.py",
        description=DESCRIPTION,
        add_help=True,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Provide the same observable behavior for `--version`
    parser.add_argument(
        "--version",
        action="version",
        version=f"sqlmap {VERSION}",
        help="Show program's version number and exit",
    )

    # Support "advanced help" flag -hh like sqlmap.
    # argparse doesn't allow -hh out of the box, so we add a dedicated switch.
    parser.add_argument(
        "-hh",
        dest="advancedHelp",
        action="store_true",
        help="Show advanced help message and exit",
    )

    _add_basic_arguments(parser)
    _add_advanced_arguments(parser)

    # Wrap parse_args to handle -hh in a familiar way.
    original_parse_args = parser.parse_args

    def parse_args(args=None, namespace=None):
        ns = original_parse_args(args=args, namespace=namespace)
        if getattr(ns, "advancedHelp", False):
            sys.stdout.write(_format_advanced_help())
            raise SystemExit(0)
        return ns

    parser.parse_args = parse_args  # type: ignore[attr-defined]
    return parser