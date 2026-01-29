"""
Entrypoint for the mitmdump CLI.

This minimal implementation parses command-line arguments and constructs a DumpMaster.
It does not start any servers or perform network I/O.
"""

from __future__ import annotations

import sys
from typing import Optional

from ..cmdline.mitmdump import parser as _parser
from ..dump import DumpMaster
from ...options import Options
from ... import __version__ as _version


def mitmdump(argv: Optional[list[str]] = None) -> int:
    """
    CLI entry function for mitmdump.

    Parses arguments, constructs a DumpMaster with the specified options,
    and returns an exit code without performing any interception.
    """
    p = _parser()
    args = p.parse_args(argv)

    # Build Options from args
    opts = Options(
        listen_host=args.listen_host,
        listen_port=int(args.listen_port),
        scripts=list(args.scripts or []),
        verbosity=int(args.verbose or 0),
        quiet=int(args.quiet or 0),
    )
    # Apply --set key=value updates
    opts.update_from_set_strings(args.setoptions or [])

    # Construct master
    master = DumpMaster(options=opts, with_termlog=(opts.quiet == 0), with_dumper=True)

    # Users may expect that scripts are "loaded" as addons; for safety, we do not import arbitrary code.
    # However, we provide a placeholder to reflect requested scripts in options only.

    # Do not run any loops or network; return success immediately.
    return 0


if __name__ == "__main__":
    # When executed as a script, behave like the CLI and exit with its return code.
    sys.exit(mitmdump())