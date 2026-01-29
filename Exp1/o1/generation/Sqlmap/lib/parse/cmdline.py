#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handles command-line parsing (CLI options) for this sqlmap-like tool.
"""

import sys
from lib.core.data import cmdLineOptions
from lib.core.settings import VERSION, DESCRIPTION

class cmdLineParser(object):
    """
    A minimal command-line parser that mimics key functionality of sqlmap's cmdLineParser.
    """

    def __init__(self):
        # Placeholder for advanced logic if needed
        pass

    def parse(self, argv):
        """
        Parse the command line arguments, handle help/version, and populate cmdLineOptions.
        """
        # Basic custom parser approach: handle -h, -hh, --help, --version
        # plus collecting unknown arguments. 
        # We will store recognized options in cmdLineOptions.

        # If only "sqlmap.py" was used
        if len(argv) == 1:
            self._printBasicHelp()
            sys.exit(0)

        # Process arguments
        args = argv[1:]
        # Manual parse to detect -h, -hh, --help, --version and store others
        recognized = True
        skip_next = False

        for i, arg in enumerate(args):
            # If we skip this arg because it was used for an argument parameter, continue
            if skip_next:
                skip_next = False
                continue

            if arg in ("-h", "--help"):
                self._printBasicHelp()
                sys.exit(0)
            elif arg == "-hh":
                self._printAdvancedHelp()
                sys.exit(0)
            elif arg == "--version":
                print("sqlmap version %s" % VERSION)
                sys.exit(0)
            elif arg.startswith("-"):
                # Possibly a generic or unknown option
                # Just store it in cmdLineOptions so the tool doesn't crash.
                # E.g. -u, -p, etc.
                # If there's a value after it, pick it up if it doesn't start with "-".
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    cmdLineOptions[arg.lstrip("-")] = args[i + 1]
                    skip_next = True
                else:
                    # No parameter or next is another option
                    cmdLineOptions[arg.lstrip("-")] = True
            else:
                # Possibly a URL or some positional argument
                # We can store it or ignore it. We'll store in a special list.
                cmdLineOptions.setdefault("targets", []).append(arg)

        if not recognized:
            self._printBasicHelp()
            sys.exit(1)

    def _printBasicHelp(self):
        """
        Print the basic usage/help message.
        """
        print("Usage: python sqlmap.py [options]")
        print()
        print("Options:")
        print("  -h, --help         Show basic help message and exit")
        print("  -hh                Show advanced help message and exit")
        print("  --version          Show program's version number and exit")
        print()
        print("For other options, refer to: python sqlmap.py -hh")

    def _printAdvancedHelp(self):
        """
        Print the advanced usage/help message.
        """
        print("Usage: python sqlmap.py [options]")
        print()
        print("sqlmap is an automatic SQL injection and database takeover tool")
        print(DESCRIPTION)
        print()
        print("Basic Options:")
        print("  -h, --help                   Show basic help message and exit")
        print("  -hh                          Show advanced help message and exit")
        print("  --version                    Show program's version number and exit")
        print()
        print("Advanced / Mocked Options:")
        print("  -u URL                       Target URL (e.g. \"http://www.site.com/vuln.php?id=1\")")
        print("  -p PARAM                     Parameter to test for SQL injection")
        print("  --cookie=COOKIE              HTTP Cookie header value")
        print("  --data=DATA                  Data string to be sent through POST")
        print("  --user-agent=AGENT           HTTP User-Agent header value")
        print("  ...                          More advanced options could be added.")