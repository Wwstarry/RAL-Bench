#!/usr/bin/env python3
import sys

from lib.core.settings import VERSION, DESCRIPTION
from lib.parse.cmdline import cmdLineParser
from lib.core.option import initOptions, init
from lib.core.data import conf
from lib.controller.controller import start


def main():
    # Parse command-line options (cmdLineParser handles -h/-hh/--version and exits when those are used)
    options = cmdLineParser()
    # Initialize global configuration with defaults and provided options
    initOptions(options)
    init()

    # If nothing actionable is provided, show a helpful message and exit gracefully
    # sqlmap upstream requires a target, but for this stub we keep benign behaviour
    actionable = any([
        getattr(conf, 'url', None),
        getattr(conf, 'data', None),
        getattr(conf, 'requestFile', None),
        getattr(conf, 'bulkFile', None),
        getattr(conf, 'logFile', None),
    ])

    if not actionable:
        # No target provided: do nothing other than an informative message
        sys.stderr.write("No target specified. Nothing to do. Use -h for basic help or -hh for advanced help.\n")
        sys.exit(2)

    # Start controller
    start()


if __name__ == "__main__":
    main()