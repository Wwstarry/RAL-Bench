"""
Main entry point for mitmproxy tools.
"""
import sys
from typing import Optional, Sequence


def mitmdump(args: Optional[Sequence[str]] = None) -> int:
    """
    The main entry point for mitmdump.
    """
    from mitmproxy.tools import cmdline
    from mitmproxy.tools.dump import DumpMaster
    
    opts = cmdline.mitmdump(args)
    
    master = DumpMaster(vars(opts))
    try:
        master.run()
    except KeyboardInterrupt:
        pass
    return 0


def mitmproxy(args: Optional[Sequence[str]] = None) -> int:
    """
    The main entry point for mitmproxy.
    """
    print("mitmproxy console UI would start here")
    return 0


def mitmweb(args: Optional[Sequence[str]] = None) -> int:
    """
    The main entry point for mitmweb.
    """
    print("mitmweb would start here")
    return 0


def run(name="mitmdump") -> int:
    """
    Run the tool with the given name.
    """
    if name == "mitmdump":
        return mitmdump(sys.argv[1:])
    elif name == "mitmproxy":
        return mitmproxy(sys.argv[1:])
    elif name == "mitmweb":
        return mitmweb(sys.argv[1:])
    else:
        return 1


if __name__ == "__main__":
    sys.exit(run())