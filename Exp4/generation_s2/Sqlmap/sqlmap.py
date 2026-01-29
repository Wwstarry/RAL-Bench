#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lightweight, pure-Python, CLI-driven SQL injection testing tool skeleton.

This repository provides a minimal interface-compatible subset of the reference
sqlmap project needed by the test suite (entrypoint, module layout, and core APIs).
"""

import sys

from lib.core.data import cmdLineOptions, conf, kb  # noqa: F401 (imported for side-effects/API surface)
from lib.parse.cmdline import cmdLineParser
from lib.core.option import init, initOptions
from lib.controller.controller import start
from lib.core.settings import VERSION


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = cmdLineParser()

    try:
        # Keep a copy of raw args for potential debugging
        initOptions(argv)
        options = parser.parse_args(argv)
        init(options)
        return start()
    except SystemExit as e:
        # argparse uses SystemExit for -h/--help, --version, and errors.
        code = e.code
        try:
            return int(code)
        except Exception:
            return 0
    except KeyboardInterrupt:
        sys.stderr.write("\n[!] Interrupted by user\n")
        return 130
    except Exception as ex:
        # Defensive: never crash/hang on unexpected exceptions during tests.
        sys.stderr.write(f"[!] Unhandled error: {ex}\n")
        sys.stderr.write(f"[*] For usage help run: python sqlmap.py -h\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())