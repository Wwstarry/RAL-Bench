from __future__ import annotations

import sys
from typing import List, Optional

from ..cmdline.mitmdump import create_parser
from ..dump import DumpMaster


def main(argv: Optional[List[str]] = None) -> int:
    """
    Console entrypoint for mitmdump.

    This minimal implementation only parses args and runs a no-op master.
    """
    if argv is None:
        argv = sys.argv[1:]
    parser = create_parser()
    args = parser.parse_args(argv)

    master = DumpMaster(options=vars(args))
    # In real mitmproxy, this would start an event loop and proxy server.
    # Here, we just simulate a run.
    return master.run()


if __name__ == "__main__":
    raise SystemExit(main())