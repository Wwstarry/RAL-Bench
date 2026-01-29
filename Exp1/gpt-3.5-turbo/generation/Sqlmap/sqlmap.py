#!/usr/bin/env python3
import sys

from lib.parse.cmdline import cmdLineParser
from lib.core.option import init, initOptions
from lib.core.data import cmdLineOptions, conf, kb
from lib.controller.controller import start
from lib.core.settings import VERSION, DESCRIPTION


def main():
    try:
        parser = cmdLineParser()
        options = parser.parse_args()

        # Handle version
        if getattr(options, "version", False):
            print(f"sqlmap version {VERSION}")
            sys.exit(0)

        # Initialize options and internal state
        init()
        initOptions(options)

        # Start controller
        start()

    except SystemExit as e:
        # argparse calls sys.exit(), allow it to exit cleanly
        raise e
    except Exception as ex:
        print(f"error: {ex}", file=sys.stderr)
        print("Use -h or --help for usage.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()