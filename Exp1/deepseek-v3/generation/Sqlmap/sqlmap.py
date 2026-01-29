#!/usr/bin/env python

"""
SQL injection testing tool (sqlmap-compatible interface)
"""

import sys
import os

# Add the lib directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from lib.parse.cmdline import cmdLineParser
from lib.core.option import initOptions
from lib.controller.controller import start

def main():
    """Main entry point"""
    try:
        # Parse command line arguments
        args = cmdLineParser()
        
        # Initialize options
        initOptions(args)
        
        # Start the controller
        start()
        
    except KeyboardInterrupt:
        print("\nUser aborted")
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()