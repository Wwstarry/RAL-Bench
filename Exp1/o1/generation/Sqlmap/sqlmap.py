#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
sqlmap.py - Main CLI entry point for the sqlmap-like tool.
This file is meant to be run directly via "python sqlmap.py [options]".
"""

import sys

from lib.parse.cmdline import cmdLineParser
from lib.core.option import init, initOptions
from lib.core.data import cmdLineOptions, conf, kb
from lib.controller.controller import start

def main():
    parser = cmdLineParser()
    parser.parse(sys.argv)
    init()
    # Initialize options (basic pass-through to conf)
    initOptions(cmdLineOptions)
    # Invoke the main controller
    start()

if __name__ == "__main__":
    main()