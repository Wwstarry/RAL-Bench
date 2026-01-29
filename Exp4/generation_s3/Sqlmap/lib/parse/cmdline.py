import argparse
import sys

from lib.core.settings import VERSION, DESCRIPTION


class _ArgumentParser(argparse.ArgumentParser):
    """
    Custom parser to keep behavior deterministic and informative, and to ensure
    no tracebacks are emitted for invalid arguments.
    """

    def error(self, message):
        # Match argparse convention: print usage then error message, exit code 2.
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\n")


def _build_parser(advanced: bool = False) -> argparse.ArgumentParser:
    epilog_lines = []
    if advanced:
        epilog_lines.extend(
            [
                "Advanced help:",
                "  This is a lightweight, test-oriented, sqlmap-compatible CLI stub.",
                "  It does not perform real SQL injection testing.",
                "",
                "Examples:",
                "  python sqlmap.py -u http://example.invalid/?id=1",
                "  python sqlmap.py --data \"id=1\" -u http://example.invalid/",
            ]
        )

    parser = _ArgumentParser(
        prog="sqlmap.py",
        add_help=True,
        description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter if advanced else argparse.HelpFormatter,
        epilog="\n".join(epilog_lines) if epilog_lines else None,
    )

    # Core/basic options used by typical harness checks
    parser.add_argument(
        "--version",
        action="version",
        version=f"sqlmap/{VERSION}",
        help="Show program's version number and exit.",
    )

    # sqlmap accepts -hh for advanced help; handle explicitly.
    parser.add_argument(
        "-hh",
        action="store_true",
        dest="advancedHelp",
        default=False,
        help="Show advanced help message and exit.",
    )

    # Minimal target options (non-functional, but recognized)
    parser.add_argument(
        "-u",
        "--url",
        dest="url",
        help="Target URL (e.g. \"http://www.site.com/vuln.php?id=1\")",
    )
    parser.add_argument(
        "--data",
        dest="data",
        help="Data string to be sent through POST (e.g. \"id=1\")",
    )

    # A couple of common switches; accepted but not implemented.
    parser.add_argument(
        "--batch",
        action="store_true",
        default=False,
        help="Never ask for user input, use default behavior.",
    )
    parser.add_argument(
        "-v",
        dest="verbose",
        type=int,
        default=1,
        help="Verbosity level: 0-6 (default 1).",
    )

    return parser


def cmdLineParser(argv=None):
    """
    Parse command line options.

    Must support: -h, -hh, --version.
    Must fail cleanly for invalid args (argparse handles that via SystemExit).
    """
    if argv is None:
        argv = sys.argv[1:]

    # If -hh is present, show advanced help and exit 0 (distinct from -h output).
    if any(arg == "-hh" for arg in argv):
        parser = _build_parser(advanced=True)
        parser.print_help(sys.stdout)
        ns = argparse.Namespace()
        ns._earlyExit = True
        ns.advancedHelp = True
        return ns

    parser = _build_parser(advanced=False)
    options = parser.parse_args(argv)

    # Normalize and sanity bounds
    try:
        if options.verbose is not None:
            options.verbose = int(options.verbose)
    except Exception:
        parser.error("argument -v: invalid int value")

    if options.verbose < 0 or options.verbose > 6:
        parser.error("argument -v: expected a value in range 0..6")

    # marker used by entrypoint
    setattr(options, "_earlyExit", False)
    return options