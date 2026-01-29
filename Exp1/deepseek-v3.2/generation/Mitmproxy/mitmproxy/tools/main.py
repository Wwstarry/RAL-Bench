"""
Main entry points for mitmproxy tools.
"""

import sys
from typing import Optional, List


def mitmdump(args: Optional[List[str]] = None) -> int:
    """
    mitmdump command line entry point.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
    
    Returns:
        Exit code
    """
    from mitmproxy.tools.cmdline import mitmdump as cmdline
    from mitmproxy.tools.dump import DumpMaster
    
    if args is None:
        args = sys.argv[1:]
    
    try:
        master = DumpMaster(cmdline.mitmdump(args))
        master.run()
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    except Exception:
        return 1