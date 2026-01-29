#!/usr/bin/env python3
"""
sqlmap.py – minimal stub entry-point that mimics the behaviour and public
interface of the original sqlmap project.

Only a (very) small subset of the full sqlmap feature set is implemented.
It is sufficient for unit-/integration tests that rely on the public API
and command-line interface existing at the expected import paths.
"""
import sys

# Ensure the local copy of the mock sqlmap library is importable when the
# entry-point is executed directly (e.g. `python sqlmap.py -h`)
if __package__ is None and __name__ == "__main__":
    # When executed as a script the CWD is the repo root, therefore we want
    # to add that directory to sys.path so that `import lib.*` works even
    # when the repo is not installed as a package.
    import pathlib
    ROOT = pathlib.Path(__file__).resolve().parent
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from lib.core.data import cmdLineOptions
from lib.core import option as core_option
from lib.parse.cmdline import cmdLineParser
from lib.controller.controller import start
from lib.core.settings import VERSION

def main(argv=None):
    """
    Main entry point for the CLI wrapper.

    1. Parse command-line arguments.
    2. Initialize global option state.
    3. Handle early-exit flags (--version / -h / -hh).
    4. Dispatch into the (mock) controller.
    """
    # 1 & 2 – parse and init
    cmdLineParser(argv=argv)
    core_option.init()

    # 3 – early returns
    if getattr(cmdLineOptions, "version", False):
        print(VERSION)
        return 0

    if getattr(cmdLineOptions, "hh", False):
        # Advanced (extra) help requested – produced by parser already.
        # The parser's `print_help()` has been called inside cmdLineParser
        # so we simply exit cleanly.
        return 0

    if getattr(cmdLineOptions, "help", False):
        # Same reasoning as above – basic help already printed.
        return 0

    # 4 – run the (mock) core functionality
    start()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        # Provide graceful termination on Ctrl-C, consistent with real tool.
        print("\n[!] user aborted")
        sys.exit(130)