#!/usr/bin/env python
import sys
from lib.core.data import cmdLineOptions
from lib.parse.cmdline import cmdLineParser
from lib.core.option import init, initOptions
from lib.controller.controller import start

def main():
    try:
        # Parse command line arguments
        args = cmdLineParser()
        
        # Update cmdLineOptions with parsed arguments
        cmdLineOptions.update(args.__dict__)
        
        # Initialize options and internal state
        initOptions(cmdLineOptions)
        init(cmdLineOptions)
        
        # Start the controller
        start()
        
    except KeyboardInterrupt:
        pass
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()