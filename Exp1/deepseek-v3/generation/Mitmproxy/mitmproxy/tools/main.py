"""Main entry points for mitmproxy tools"""

import sys
from typing import List, Optional

def mitmdump(args: Optional[List[str]] = None) -> int:
    """mitmdump CLI entry function"""
    from mitmproxy.tools.cmdline import mitmdump as parse_args
    from mitmproxy.tools.dump import DumpMaster
    
    try:
        options = parse_args(args)
        master = DumpMaster(options)
        master.run()
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1