"""
Command-line interface specification for mitmdump.

This module exposes a function parser() that returns an argparse.ArgumentParser
with a minimal set of options compatible with common mitmdump invocations.
"""

from __future__ import annotations

import argparse
from typing import Optional
from ... import __version__ as _version


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mitmdump",
        description="mitmdump: a minimal, safe-to-evaluate subset of mitmproxy's command-line dump tool.",
        add_help=True,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # Version
    p.add_argument("--version", action="version", version=f"mitmdump {_version}")

    # Listen options
    p.add_argument("--listen-host", dest="listen_host", default="127.0.0.1", help="Proxy listen interface.")
    p.add_argument(
        "-p",
        "--listen-port",
        dest="listen_port",
        type=int,
        default=8080,
        help="Proxy listen port.",
    )

    # Scripting and options
    p.add_argument(
        "-s",
        "--scripts",
        dest="scripts",
        action="append",
        default=[],
        metavar="PATH",
        help="Execute a script. Can be passed multiple times.",
    )
    p.add_argument(
        "--set",
        dest="setoptions",
        action="append",
        default=[],
        metavar="key=value",
        help="Set an option. Can be passed multiple times.",
    )

    # I/O options (no real I/O in this subset; accepted for compatibility)
    p.add_argument("-r", "--read-file", dest="rfile", default=None, help="Read flows from file.")
    p.add_argument("-w", "--write-file", dest="wfile", default=None, help="Write flows to file.")

    # Verbosity flags
    p.add_argument(
        "-q",
        "--quiet",
        dest="quiet",
        action="count",
        default=0,
        help="Quiet output; can be specified multiple times.",
    )
    p.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="count",
        default=0,
        help="Increase verbosity; can be specified multiple times.",
    )

    # Upstream mode placeholder
    p.add_argument(
        "-U",
        "--upstream-server",
        dest="upstream_server",
        default=None,
        help="Use upstream proxy specified as scheme://host[:port].",
    )

    return p


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    return parser().parse_args(argv)