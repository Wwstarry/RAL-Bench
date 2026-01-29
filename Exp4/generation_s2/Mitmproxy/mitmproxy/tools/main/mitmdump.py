from __future__ import annotations

import sys
from typing import List, Optional

from mitmproxy import __version__
from mitmproxy.tools.cmdline import mitmdump as cmd_mitmdump
from mitmproxy.tools.dump import DumpMaster


def mitmdump(argv: Optional[List[str]] = None) -> int:
    """
    CLI entry function for mitmdump.

    This is intentionally safe: no network operations are performed.
    """
    opts = cmd_mitmdump.parse_args(argv=argv, prog="mitmdump")
    if opts.version:
        sys.stdout.write(__version__ + "\n")
        return 0
    m = DumpMaster(options=opts)
    return int(m.run() or 0)


def main() -> None:
    raise SystemExit(mitmdump(sys.argv[1:]))


if __name__ == "__main__":
    main()