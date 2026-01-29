from __future__ import annotations

from typing import List, Optional

from mitmproxy.options import Options
from mitmproxy.tools.cmdline.mitmdump import parse_args
from mitmproxy.tools.dump import DumpMaster


def _options_from_namespace(ns) -> Options:
    # Keep this mapping explicit and minimal for determinism.
    return Options(
        quiet=bool(getattr(ns, "quiet", False)),
        verbose=int(getattr(ns, "verbose", 0) or 0),
        listen_host=str(getattr(ns, "listen_host", "")),
        listen_port=int(getattr(ns, "listen_port", 8080)),
        mode=str(getattr(ns, "mode", "regular")),
        confdir=str(getattr(ns, "confdir", "")),
        scripts=list(getattr(ns, "scripts", []) or []),
        set=list(getattr(ns, "set", []) or []),
    )


def mitmdump(argv: Optional[List[str]] = None) -> int:
    ns = parse_args(argv)
    opts = _options_from_namespace(ns)
    master = DumpMaster(options=opts)
    master.run()
    return 0


def mitmproxy(argv: Optional[List[str]] = None) -> int:
    # Minimal stub: parse same args and exit after running a no-op master.
    return mitmdump(argv)


def mitmweb(argv: Optional[List[str]] = None) -> int:
    # Minimal stub: parse same args and exit after running a no-op master.
    return mitmdump(argv)