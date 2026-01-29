#!/usr/bin/env python

"""
Copyright (c) 2023 SQLmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import sys
import time
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Define application paths
sys.path.append(sys.path[0])

try:
    from lib.parse.cmdline import cmdLineParser
    from lib.core.common import banner, setPaths, weAreFrozen
    from lib.core.data import logger, paths
    from lib.core.settings import VERSION
    from lib.core.option import init
    from lib.controller.controller import start
except KeyboardInterrupt:
    print("\nAborted")
    sys.exit(1)
except ImportError as e:
    print(f"Error importing module: {e}")
    sys.exit(1)

def main():
    """
    Main function of sqlmap when running from command line.
    """
    try:
        setPaths(sys.path[0])
        
        # Parse command line arguments
        cmdLineOptions = cmdLineParser()
        
        # Initialize options
        init()

        if not any(sys.argv[1:]):
            banner()
            print("[!] No arguments specified, use -h for basic help")
            sys.exit(1)

        # Start the controller
        start()

    except KeyboardInterrupt:
        print("\nAborted")
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as ex:
        print(f"\nUnhandled exception: {ex}")
        sys.exit(1)
    finally:
        # Reference cleanup
        pass

if __name__ == "__main__":
    main()