#!/usr/bin/env python

"""
sqlmap - automatic SQL injection and database takeover tool
"""

import sys
import os

# Add the current directory to the path so we can import lib modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.core.data import cmdLineOptions, conf, kb, logger
from lib.core.option import init, initOptions
from lib.parse.cmdline import cmdLineParser
from lib.controller.controller import start
from lib.core.settings import VERSION, DESCRIPTION
from lib.core.common import setPaths, banner


def main():
    """
    Main function of sqlmap
    """
    try:
        # Set paths for the application
        setPaths()
        
        # Parse command line options
        cmdLineOptions.update(cmdLineParser().__dict__)
        
        # Initialize options
        initOptions(cmdLineOptions)
        
        # Initialize the rest of the environment
        init()
        
        # Start the controller
        start()
        
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\n[!] User quit")
        sys.exit(1)
    except Exception as e:
        print("[!] Error: %s" % str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()