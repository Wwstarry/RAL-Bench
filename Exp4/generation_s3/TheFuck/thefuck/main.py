from __future__ import annotations

import argparse
import sys

from . import __version__
from .corrector import get_corrected_commands
from .settings import as_settings
from .types import Command


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="thefuck", add_help=True)
    p.add_argument("-l", "--list", action="store_true", help="list all suggestions")
    p.add_argument("--version", action="store_true", help="print version and exit")
    p.add_argument("--debug", action="store_true", help="debug output to stderr")

    # Explicit injection of prior command (used by tests).
    p.add_argument("--command", dest="command", default=None, help="command script")
    p.add_argument("--stdout", dest="stdout", default="", help="previous stdout")
    p.add_argument("--stderr", dest="stderr", default="", help="previous stderr")
    p.add_argument(
        "--returncode", dest="returncode", default=None, type=int, help="previous return code"
    )

    # Fallback: remaining args are treated as the script.
    p.add_argument("script", nargs=argparse.REMAINDER, help="script to correct")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()

    try:
        ns = parser.parse_args(argv)
    except SystemExit as e:
        # argparse already printed error/help; propagate code.
        return int(getattr(e, "code", 2) or 2)

    if ns.version:
        sys.stdout.write(f"{__version__}\n")
        return 0

    settings = as_settings({"debug": bool(ns.debug), "no_interactive": True})

    if ns.command is not None:
        script = ns.command
        stdout = ns.stdout or ""
        stderr = ns.stderr or ""
        returncode = 1 if ns.returncode is None else int(ns.returncode)
    else:
        # Remainder includes possible leading "--" depending on how invoked.
        rem = list(ns.script or [])
        if rem and rem[0] == "--":
            rem = rem[1:]
        script = " ".join(rem).strip()
        stdout = ""
        stderr = ""
        returncode = 1

    if not script:
        # No input; do not prompt.
        return 1

    cmd = Command(script=script, stdout=stdout, stderr=stderr, returncode=returncode)
    suggestions = get_corrected_commands(cmd, settings=settings)

    if not suggestions:
        return 1

    if ns.list:
        sys.stdout.write("\n".join(suggestions) + "\n")
    else:
        sys.stdout.write(suggestions[0] + "\n")
    return 0