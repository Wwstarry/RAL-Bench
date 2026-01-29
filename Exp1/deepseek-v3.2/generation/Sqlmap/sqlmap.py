#!/usr/bin/env python

"""
SQL injection testing tool
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.parse.cmdline import cmdLineParser
from lib.core.option import initOptions
from lib.controller.controller import start

def main():
    """Main entry point for the SQL injection testing tool"""
    try:
        # Parse command line arguments
        parser = cmdLineParser()
        args = parser.parse_args()
        
        # Initialize options
        initOptions(args)
        
        # Start the controller
        start()
        
    except SystemExit:
        # This handles argparse's help/version exits
        pass
    except KeyboardInterrupt:
        print("\n[*] User interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"[!] Unhandled exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()