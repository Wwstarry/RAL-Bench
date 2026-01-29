#!/usr/bin/env python3
import sys

from lib.parse.cmdline import cmdLineParser
from lib.core.option import initOptions, init
from lib.controller.controller import start


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    try:
        options = cmdLineParser(argv)
    except SystemExit as ex:
        # argparse uses SystemExit for -h/--help and for parsing errors.
        # Let it propagate as a clean CLI exit.
        return int(ex.code) if ex.code is not None else 0

    # Initialize shared runtime state
    initOptions(options)
    init(options)

    # If parser marked an early termination (e.g., -hh handled without argparse exit)
    if getattr(options, "_earlyExit", False):
        return 0

    try:
        ret = start()
    except SystemExit as ex:
        return int(ex.code) if ex.code is not None else 0
    except Exception as ex:
        # Defensive: never show a traceback in typical harness runs.
        sys.stderr.write(f"ERROR: {ex}\n")
        return 1

    return 0 if ret is None else int(ret)


if __name__ == "__main__":
    raise SystemExit(main())