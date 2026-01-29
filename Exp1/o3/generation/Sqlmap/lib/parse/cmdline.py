"""
`lib.parse.cmdline` – command-line parser implementation.
It exposes *cmdLineParser*, mirroring the reference project.
"""
import argparse
import sys
from lib.core.data import cmdLineOptions
from lib.core.settings import DESCRIPTION, VERSION

_ADVANCED_HELP = f"""
{DESCRIPTION}

Advanced (extra) help
--------------------
sqlmap.py [options]

Basic options:
  -u URL, --url=URL           Target URL (e.g. "http://www.site.com/vuln.php?id=1")
  -p PARAMETER                Testable parameter(s)

Miscellaneous:
  -hh                         Show this advanced help message
  --version                   Show program's version number and exit
"""

def _build_parser():
    """
    Construct and return a configured argparse.ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="sqlmap.py",
        description=DESCRIPTION,
        add_help=False,     # We will add our own -h handler to mimic sqlmap.
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Basic help (-h).
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        dest="help",
        help="Show basic help message and exit",
    )

    # Advanced help (-hh)
    parser.add_argument(
        "-hh",
        action="store_true",
        dest="hh",
        help="Show advanced help message and exit",
    )

    # Version
    parser.add_argument(
        "--version",
        action="store_true",
        dest="version",
        help="Show program's version number and exit",
    )

    # Collect unknown args so we can report them uniformly (argparse would
    # already do that, but capturing here allows us finer control).
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help=argparse.SUPPRESS,
    )
    return parser

def cmdLineParser(argv=None):
    """
    Parse *argv* (defaults to sys.argv[1:]) and store result in
    ``lib.core.data.cmdLineOptions``.

    Returns the populated Namespace instance.
    """
    global cmdLineOptions

    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()

    # argparse exits on error automatically; calling `parse_known_args`
    # allows us to detect/handle unknown options ourselves to provide
    # friendlier feedback.
    parsed, unknown = parser.parse_known_args(argv)

    # If user supplied unknown/unsupported options we treat that as a fatal
    # argument error but present a helpful usage hint.
    if unknown:
        parser.print_usage(sys.stderr)
        sys.stderr.write(
            f"sqlmap.py: error: unrecognized arguments: {' '.join(unknown)}\n"
        )
        sys.exit(2)

    # Store globally for rest of program/tests
    cmdLineOptions = parsed

    # Handle help/version flags immediately so higher-level code doesn't have
    # to duplicate this logic.
    if parsed.help:
        parser.print_help()
        sys.exit(0)

    if parsed.hh:
        # Print advanced help
        print(_ADVANCED_HELP)
        sys.exit(0)

    if parsed.version:
        # The top-level entrypoint handles printing the version – nothing to
        # do here.
        pass

    return parsed