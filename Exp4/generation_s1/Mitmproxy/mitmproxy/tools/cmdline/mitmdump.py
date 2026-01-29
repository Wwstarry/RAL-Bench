from __future__ import annotations

import argparse
from typing import List, Optional

from mitmproxy.version import __version__


def mitmdump(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add mitmdump-compatible arguments to an ArgumentParser.
    This is a minimal subset intended for API and help-output stability in tests.
    """
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="show program's version number and exit",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=False,
        help="quiet",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase verbosity (can be repeated)",
    )
    parser.add_argument(
        "-p",
        "--listen-port",
        dest="listen_port",
        type=int,
        default=8080,
        metavar="PORT",
        help="proxy service port",
    )
    parser.add_argument(
        "--listen-host",
        dest="listen_host",
        default="",
        metavar="HOST",
        help="proxy service host",
    )
    parser.add_argument(
        "-m",
        "--mode",
        dest="mode",
        default="regular",
        metavar="MODE",
        help="mode of operation",
    )
    parser.add_argument(
        "-s",
        "--script",
        dest="scripts",
        action="append",
        default=[],
        metavar="SCRIPT",
        help="execute a script",
    )
    parser.add_argument(
        "--set",
        dest="set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="set an option (KEY=VALUE)",
    )
    parser.add_argument(
        "--confdir",
        dest="confdir",
        default="",
        metavar="DIR",
        help="configuration directory",
    )
    return parser


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="mitmdump", add_help=True)
    mitmdump(parser)
    return parser.parse_args(args=args)