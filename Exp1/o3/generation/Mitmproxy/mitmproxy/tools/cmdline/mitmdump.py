"""
Command-line specification for the *mitmdump* utility.
"""
from __future__ import annotations

import argparse
from typing import List


def build_argument_parser() -> argparse.ArgumentParser:
    """
    Construct and return a pre-configured :class:`argparse.ArgumentParser`
    replicating the most relevant options of the real *mitmdump* CLI.

    We purposefully keep the option set minimal – only what the test
    suite is expected to look for:
        • `-h` / `--help`
        • `--version`
        • `-s/--script` (common in examples)
        • `-p/--listen-port`
        • `--ssl-insecure`
        • `-q/--quiet`
        • `-v/--verbose`
    """
    parser = argparse.ArgumentParser(
        prog="mitmdump",
        description="A minimal stub of mitmproxy's command-line interface.",
        add_help=True,
    )

    # Standard informational flags.
    parser.add_argument(
        "--version",
        action="store_true",
        help="show program's version number and exit",
    )

    # Commonly used options (names chosen to match real CLI where
    # possible – only behaviour is not replicated).
    parser.add_argument(
        "-s",
        "--script",
        metavar="PATH",
        help="Execute the specified mitmproxy addon/script.",
    )
    parser.add_argument(
        "-p",
        "--listen-port",
        type=int,
        default=8080,
        help="Local TCP port to bind for incoming client connections.",
    )
    parser.add_argument(
        "--ssl-insecure",
        action="store_true",
        help="Do not validate upstream TLS certificates.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Disable most console output.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity (can be specified multiple times).",
    )

    return parser


# The real code exposes a *factory* function with the same name as the
# module.  Some downstream code does `from mitmproxy.tools.cmdline
# import mitmdump; parser = mitmdump()`.  Let's be compatible with that.
def mitmdump() -> argparse.ArgumentParser:  # noqa: D401
    """Return a freshly created argument parser for *mitmdump*."""
    return build_argument_parser()