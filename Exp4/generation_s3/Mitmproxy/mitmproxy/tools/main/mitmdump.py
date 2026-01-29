from __future__ import annotations

from typing import Optional, Sequence

from mitmproxy.options import Options
from mitmproxy.tools.cmdline.mitmdump import parse_args
from mitmproxy.tools.dump import DumpMaster


def mitmdump(argv: Optional[Sequence[str]] = None) -> int:
    """
    Minimal mitmdump entry function.

    - Parses args.
    - Instantiates DumpMaster.
    - Runs and shuts down without doing any network activity.
    """
    try:
        args = parse_args(argv)
    except SystemExit as e:
        # argparse uses SystemExit for --help and invalid args.
        code = e.code
        return int(code) if isinstance(code, int) else 0

    options = Options(
        listen_port=int(getattr(args, "listen_port", 8080)),
        quiet=bool(getattr(args, "quiet", False)),
        verbose=bool(getattr(args, "verbose", False)),
        script=getattr(args, "script", None),
    )
    options.apply_set(getattr(args, "set", []) or [])

    master = DumpMaster(options)
    started = False
    try:
        master.run()
        started = True
        return 0
    finally:
        if started:
            master.shutdown()