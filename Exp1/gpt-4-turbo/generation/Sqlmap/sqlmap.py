#!/usr/bin/env python3
import sys
import os

# Ensure the repo root is in sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.parse.cmdline import cmdLineParser
from lib.core.option import init, initOptions
from lib.core.data import cmdLineOptions, conf, kb
from lib.core.settings import VERSION, DESCRIPTION
from lib.controller.controller import start

def main():
    try:
        cmdLineParser()
        initOptions(cmdLineOptions)
        init(cmdLineOptions)
        start()
    except SystemExit as e:
        # argparse exits with SystemExit; propagate
        raise
    except Exception as e:
        print(f"[CRITICAL] Unhandled exception: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()