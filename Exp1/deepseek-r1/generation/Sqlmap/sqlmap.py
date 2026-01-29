#!/usr/bin/env python

"""
Copyright (c) 2006-2024 sqlmap developers (https://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import sys

# Ensure we can import from lib directory
sys.path.insert(0, '.')

from lib.core.data import cmdLineOptions
from lib.core.option import initOptions
from lib.controller.controller import start

def main():
    try:
        # Parse command line arguments
        from lib.parse.cmdline import cmdLineParser
        cmdLineOptions.update(cmdLineParser().__dict__)
        
        # Initialize options
        initOptions()
        
        # Start the controller
        start()
        
    except KeyboardInterrupt:
        print("\n[*] User aborted")
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        print(f"\n[!] Unhandled exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()