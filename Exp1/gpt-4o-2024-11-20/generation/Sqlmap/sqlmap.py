#!/usr/bin/env python

import sys
from lib.parse.cmdline import cmdLineParser
from lib.core.option import init, initOptions
from lib.controller.controller import start
from lib.core.data import cmdLineOptions, conf, kb
from lib.core.settings import VERSION, DESCRIPTION

def main():
    try:
        # Parse command-line arguments
        cmdLineParser()
        
        # Initialize options and configuration
        initOptions(cmdLineOptions)
        init()
        
        # Start the main controller logic
        start()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()