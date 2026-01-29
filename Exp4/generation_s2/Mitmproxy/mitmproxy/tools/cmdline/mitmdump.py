from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Options:
    """
    Minimal options container used by frontends.
    """
    quiet: bool = False
    verbose: bool = False
    version: bool = False
    addons: List[Any] = field(default_factory=list)


def make_parser(prog: str = "mitmdump") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        add_help=True,
        description="Minimal mitmdump-compatible frontend (safe subset).",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="quiet output")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("--version", action="store_true", help="show version and exit")
    return parser


def parse_args(argv: Optional[List[str]] = None, prog: str = "mitmdump") -> Options:
    parser = make_parser(prog=prog)
    ns = parser.parse_args(argv)
    return Options(quiet=bool(ns.quiet), verbose=bool(ns.verbose), version=bool(ns.version))