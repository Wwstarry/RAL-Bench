"""
Entry-point wrapper for the *mitmdump* CLI tool.

The real mitmproxy distribution installs this under the name `mitmdump`
into the user’s PATH via `console_scripts`.  Here we only need the
callable to exist so that tests can invoke it.
"""
from __future__ import annotations

import sys
from typing import List, Sequence

from ..dump import DumpMaster
from ..cmdline.mitmdump import build_argument_parser


def mitmdump(argv: Sequence[str] | None = None) -> int:
    """
    Start a *very* small facsimile of mitmdump.

    Parameters
    ----------
    argv:
        List/tuple of CLI arguments **excluding** the executable name.
        If *None*, :pymod:`sys.argv` (without argv[0]) is used.

    Returns
    -------
    int
        Exit status code.  `0` on success, non-zero on (simulated) error.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = build_argument_parser()
    args = parser.parse_args(argv)

    # Handle the ultra-common `--version` early and bail out.  This
    # mirrors the behaviour of the real mitmproxy CLI.
    if getattr(args, "version", False):
        print(f"mitmdump {sys.modules['mitmproxy'].__version__}")
        return 0

    # Instantiate our stub DumpMaster with the parsed arguments.
    master = DumpMaster(options=vars(args))

    # In the real tool the master would connect to the event-loop etc.
    # We just immediately "run" and return the exit code.
    try:
        return master.run()
    finally:
        master.shutdown()


# Allow `python -m mitmproxy.tools.main.mitmdump` to work.
def main() -> None:  # noqa: D401
    sys.exit(mitmdump())