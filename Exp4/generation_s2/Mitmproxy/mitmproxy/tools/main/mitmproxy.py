from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from mitmproxy import __version__


def make_parser(prog: str = "mitmproxy") -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=prog,
        add_help=True,
        description="Minimal mitmproxy console UI frontend (safe subset).",
    )
    p.add_argument("--version", action="store_true", help="show version and exit")
    return p


def mitmproxy(argv: Optional[List[str]] = None) -> int:
    ns = make_parser().parse_args(argv)
    if ns.version:
        sys.stdout.write(__version__ + "\n")
        return 0
    # No interactive UI implemented in this safe subset.
    sys.stdout.write("mitmproxy (safe subset): UI not implemented.\n")
    return 0


def main() -> None:
    raise SystemExit(mitmproxy(sys.argv[1:]))


if __name__ == "__main__":
    main()