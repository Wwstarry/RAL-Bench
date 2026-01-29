#!/usr/bin/env python

"""
Copyright (c) 2023 SQLmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import argparse
import os
import sys

from lib.core.common import banner
from lib.core.data import cmdLineOptions, logger
from lib.core.settings import VERSION, DESCRIPTION

def cmdLineParser():
    """
    Parse the command line arguments
    """
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )

    # Target options
    target = parser.add_argument_group("Target")
    target.add_argument("-u", "--url", dest="url", help="Target URL")
    target.add_argument("-d", "--direct", dest="direct", help="Connection string for direct database connection")

    # Request options
    request = parser.add_argument_group("Request")
    request.add_argument("--data", dest="data", help="Data string to be sent through POST")
    request.add_argument("--cookie", dest="cookie", help="HTTP Cookie header value")
    
    # Detection options
    detection = parser.add_argument_group("Detection")
    detection.add_argument("--level", dest="level", type=int, default=1, help="Level of tests to perform (1-5, default 1)")
    detection.add_argument("--risk", dest="risk", type=int, default=1, help="Risk of tests to perform (1-3, default 1)")
    
    # Injection options
    injection = parser.add_argument_group("Injection")
    injection.add_argument("--technique", dest="tech", help="SQL injection techniques to use (default: BEUSTQ)")
    
    # Miscellaneous options
    misc = parser.add_argument_group("Miscellaneous")
    misc.add_argument("-h", "--help", dest="help", action="store_true", help="Show basic help message and exit")
    misc.add_argument("-hh", "--advanced-help", dest="advHelp", action="store_true", help="Show advanced help message and exit")
    misc.add_argument("--version", dest="version", action="store_true", help="Show program's version number and exit")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle special cases
    if args.version:
        print(f"sqlmap version {VERSION}")
        sys.exit(0)
    
    if args.help:
        banner()
        parser.print_help()
        sys.exit(0)
    
    if args.advHelp:
        banner()
        parser.print_help()
        print("\nAdvanced Options:")
        print("  These options provide more detailed control over the testing process.")
        print("  For complete documentation, visit: http://sqlmap.org/")
        sys.exit(0)
    
    # Save parsed arguments to the global data container
    cmdLineOptions.update(vars(args))
    
    return cmdLineOptions