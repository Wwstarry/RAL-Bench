#!/usr/bin/env python3
import sys

from lib.core.data import cmdLineOptions, conf, kb
from lib.parse.cmdline import cmdLineParser
from lib.core.option import init, initOptions
from lib.controller.controller import start
from lib.core.settings import VERSION, DESCRIPTION


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    try:
        parser = cmdLineParser()
        # Parse args. argparse will handle -h/--help and error formatting.
        args = parser.parse_args(argv)

        # Handle --version explicitly to match expected behavior
        if getattr(args, "version", False):
            sys.stdout.write(f"sqlmap/{VERSION}\n")
            return 0

        # Store parsed options
        cmdLineOptions.clear()
        cmdLineOptions.update(vars(args))

        # Initialize options/state (lightweight)
        initOptions(cmdLineOptions)
        init()

        # Run controller
        return start()

    except SystemExit as se:
        # argparse uses SystemExit for help and parse errors; treat as clean exit
        return int(se.code) if isinstance(se.code, int) else 0
    except Exception as ex:
        sys.stderr.write(f"[CRITICAL] unhandled exception: {ex}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())