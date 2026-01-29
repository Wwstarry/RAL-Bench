#!/usr/bin/env python3
import sys

from lib.core.settings import VERSION, DESCRIPTION
from lib.parse.cmdline import cmdLineParser
from lib.core.option import init, initOptions
from lib.controller.controller import start


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    # Mirror typical CLI behavior: show help when no args were supplied
    if not argv:
        parser = cmdLineParser(build_only=True)
        parser.print_help(sys.stdout)
        return 0

    # Normal flow: parse/initialize/start
    init(argv)
    initOptions()
    start()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        # argparse and internal clean exits should propagate without tracebacks
        raise
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted by user\n")
        raise SystemExit(130)
    except Exception as ex:
        sys.stderr.write(f"Critical error: {ex}\n")
        raise SystemExit(1)