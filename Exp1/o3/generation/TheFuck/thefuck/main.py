"""
Very small wrapper that turns ``thefuck`` into a non-interactive one-shot CLI
tool that prints a single suggestion (or optionally all of them).

The interface is *greatly* simplified compared to the real project but is
sufficient for the test-suite:

    $ python -m thefuck --command "git sl" --stderr "git: 'sl' is not a git command" --exit 1

Options
-------
--command/-c   The command line that failed. (mandatory)
--stdout / -o  Stdout that the failed command produced.
--stderr / -e  Stderr that the failed command produced.
--exit   / -x  Exit status (int). Default: 1
--all    / -a  Print *all* suggestions, not just the first.
--help         Show help and exit(0)

The function :pyfunc:`thefuck.main.main` is designed to be imported and called
directly by the test-suite – it returns an *int* exit-status.
"""
from __future__ import annotations

import argparse
import sys

from .command import Command
from .corrector import get_corrected_commands


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="thefuck",
        description="Tiny re-implementation of The Fuck – non-interactive variant",
        add_help=False,
    )
    parser.add_argument("--help", action="help", help="Show this help message and exit.")
    parser.add_argument("-c", "--command", required=True, help="The command that failed.")
    parser.add_argument("-o", "--stdout", default="", help="Stdout of the failed command.")
    parser.add_argument("-e", "--stderr", default="", help="Stderr of the failed command.")
    parser.add_argument(
        "-x",
        "--exit",
        type=int,
        default=1,
        dest="exit_code",
        help="Exit status of the failed command.",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Print ALL suggestions (default: only best).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Entry-point used both by ``python -m thefuck`` and by the test-suite.

    Parameters
    ----------
    argv:
        Raw argument list (excluding argv[0]).  When *None*, use
        :pydata:`sys.argv[1:]`.

    Returns
    -------
    int
        Conventional POSIX exit-status – 0 == success.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()
    ns = parser.parse_args(argv)

    # Build Command object from CLI input
    cmd = Command(
        script=ns.command,
        stdout=ns.stdout,
        stderr=ns.stderr,
        exit_code=ns.exit_code,
    )

    candidates = get_corrected_commands(cmd)
    if not candidates:
        # Nothing to do – no suggestion found
        print("No suggestion found.", file=sys.stderr)
        return 1

    if ns.all:
        for c in candidates:
            print(c.fixed_script)
    else:
        # Only best candidate
        print(candidates[0].fixed_script)

    return 0