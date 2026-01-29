"""
Main entry point for mitmproxy tools.
"""

import sys
from typing import Optional, List


def mitmdump(args: Optional[List[str]] = None) -> int:
    """
    Entry point for mitmdump CLI tool.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
    
    Returns:
        Exit code (0 for success)
    """
    if args is None:
        args = sys.argv[1:]
    
    # Import here to avoid circular dependencies
    from mitmproxy.tools.dump import DumpMaster
    from mitmproxy.tools.cmdline import mitmdump as mitmdump_cmdline
    
    parser = mitmdump_cmdline()
    opts = parser.parse_args(args)
    
    master = DumpMaster(opts)
    try:
        master.run()
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1