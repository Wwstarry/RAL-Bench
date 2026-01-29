from __future__ import annotations

import argparse
import sys
from typing import Sequence

from .corrector import get_best_suggestion, get_suggestions
from .rules import load_rules
from .settings import Settings
from .types import Command
from . import __version__


def get_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="thefuck", add_help=True)
    p.add_argument("--version", action="store_true", help="Print version and exit")
    p.add_argument("--command", help="Previous command as a single string")
    p.add_argument("--stdout", default="", help="Captured stdout of previous command")
    p.add_argument("--stderr", default="", help="Captured stderr of previous command")
    p.add_argument("--exit-code", type=int, default=0, help="Exit code of previous command")
    p.add_argument("--script", default="", help="Shell/script name")
    p.add_argument("--best", action="store_true", help="Print only the best suggestion")
    p.add_argument(
        "--suggest",
        action="store_true",
        help="Print suggestions one per line (default if not --best)",
    )
    p.add_argument("-n", "--no-confirm", action="store_true", default=True, help="Non-interactive mode")
    p.add_argument("cmd", nargs=argparse.REMAINDER, help="Previous command (positional fallback)")
    return p


def _command_from_args(ns: argparse.Namespace) -> Command:
    cmd = ns.command
    if (cmd is None or cmd == "") and ns.cmd:
        # argparse REMAINDER may include leading '--' if used; keep joined.
        cmd = " ".join(ns.cmd).strip()
    cmd = cmd or ""
    return Command(
        script=ns.script or "",
        command=cmd,
        stdout=ns.stdout or "",
        stderr=ns.stderr or "",
        return_code=int(ns.exit_code),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = get_parser()
    ns = parser.parse_args(list(argv) if argv is not None else None)

    if ns.version:
        sys.stdout.write(f"{__version__}\n")
        return 0

    settings = Settings(non_interactive=bool(ns.no_confirm), require_confirmation=False)
    rules = load_rules(settings=settings)
    command = _command_from_args(ns)

    # If previous command succeeded, do not suggest.
    if command.return_code == 0:
        return 1

    if ns.best:
        best = get_best_suggestion(command, rules, settings=settings)
        if best:
            sys.stdout.write(best + "\n")
            return 0
        return 1

    # Default to --suggest behavior when neither specified.
    suggestions = get_suggestions(command, rules, settings=settings)
    if suggestions:
        sys.stdout.write("\n".join(suggestions) + "\n")
        return 0
    return 1