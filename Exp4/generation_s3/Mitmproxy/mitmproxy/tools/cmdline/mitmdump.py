from __future__ import annotations

import argparse
from typing import Optional, Sequence

from mitmproxy import __version__


def get_version() -> str:
    return f"mitmproxy {__version__}"


def make_parser(prog: str = "mitmdump") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        add_help=True,
        description="Minimal mitmdump-compatible CLI (safe stub).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=get_version(),
        help="show program's version number and exit",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=False,
        help="suppress non-error output (stub)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="increase verbosity (stub)",
    )
    parser.add_argument(
        "-s",
        "--script",
        dest="script",
        metavar="PATH",
        default=None,
        help="script to load (parsed only; not executed)",
    )
    parser.add_argument(
        "-p",
        "--listen-port",
        dest="listen_port",
        type=int,
        default=8080,
        help="listening port (no actual listening in this stub)",
    )
    parser.add_argument(
        "--set",
        dest="set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="set an option (may be repeated)",
    )
    return parser


def parse_args(argv: Optional[Sequence[str]] = None, *, prog: str = "mitmdump") -> argparse.Namespace:
    parser = make_parser(prog=prog)
    return parser.parse_args(args=argv)