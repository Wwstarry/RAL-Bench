from __future__ import annotations

import argparse


def create_parser() -> argparse.ArgumentParser:
    """
    Create an argparse parser for mitmdump.

    This is intentionally a small subset focused on stable help output and
    basic option names commonly referenced by tooling/tests.
    """
    p = argparse.ArgumentParser(
        prog="mitmdump",
        add_help=True,
        description="Minimal mitmdump (safe subset; no real interception).",
    )

    # Commonly referenced mitmproxy/mitmdump flags (subset).
    p.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Quiet mode (no event log).",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity. Can be specified multiple times.",
    )
    p.add_argument(
        "-p",
        "--listen-port",
        type=int,
        default=8080,
        help="Port to listen on (no-op in this subset).",
    )
    p.add_argument(
        "--listen-host",
        default="127.0.0.1",
        help="Host to listen on (no-op in this subset).",
    )
    p.add_argument(
        "-s",
        "--script",
        action="append",
        default=[],
        help="Add script/addon (accepted but not executed in this subset).",
    )
    p.add_argument(
        "--set",
        dest="set_options",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Set an option (accepted; stored as raw strings).",
    )
    p.add_argument(
        "--version",
        action="version",
        version="mitmproxy 0.0.0",
    )
    return p