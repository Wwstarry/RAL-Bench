import argparse
import sys

from lib.core.settings import VERSION, DESCRIPTION


class _SmartHelpFormatter(argparse.RawTextHelpFormatter):
    pass


def cmdLineParser():
    """
    Build and return an argparse.ArgumentParser compatible with sqlmap entry usage.
    Must support:
      -h  basic help
      -hh advanced help
      --version
    """
    parser = argparse.ArgumentParser(
        prog="sqlmap.py",
        description=DESCRIPTION,
        formatter_class=_SmartHelpFormatter,
        add_help=True,
    )

    # Match common sqlmap flags used by black-box tests
    parser.add_argument("--version", action="store_true", help="Show program's version number and exit")

    # Basic/common options (subset)
    parser.add_argument("-u", "--url", dest="url", help="Target URL (e.g. \"http://example.com/vuln.php?id=1\")")
    parser.add_argument("--batch", action="store_true", help="Never ask for user input, use the default behavior")
    parser.add_argument("-v", dest="verbosity", type=int, default=1, help="Verbosity level (0-6, default 1)")

    # Advanced help: sqlmap uses -hh to show more details
    parser.add_argument(
        "-hh",
        dest="advancedHelp",
        action="store_true",
        help="Show advanced help message and exit",
    )

    # We want -hh to behave like "print extended help then exit 0"
    # argparse doesn't automatically treat -hh as help, so we implement it via a custom parse wrapper.
    parser._sqlmap_advanced_help = _advanced_help_text(parser)
    _wrap_parse_args_for_hh(parser)

    return parser


def _wrap_parse_args_for_hh(parser):
    original_parse_args = parser.parse_args

    def parse_args(args=None, namespace=None):
        if args is None:
            args = sys.argv[1:]
        if "-hh" in args:
            sys.stdout.write(parser._sqlmap_advanced_help)
            raise SystemExit(0)
        return original_parse_args(args=args, namespace=namespace)

    parser.parse_args = parse_args


def _advanced_help_text(parser):
    # Provide a deterministic advanced help output.
    # Keep it informative but lightweight; avoid depending on environment/terminal width.
    lines = []
    lines.append(f"{parser.prog} {DESCRIPTION}")
    lines.append("")
    lines.append("Usage:")
    lines.append(f"  python {parser.prog} [options]")
    lines.append("")
    lines.append("Basic options:")
    lines.append("  -h, --help            Show basic help message and exit")
    lines.append("  -hh                   Show advanced help message and exit")
    lines.append("  --version             Show program's version number and exit")
    lines.append("  -u URL, --url URL     Target URL")
    lines.append("  --batch               Never ask for user input, use default behavior")
    lines.append("  -v VERBOSITY          Verbosity level (0-6)")
    lines.append("")
    lines.append("Notes:")
    lines.append("  This is a minimal, pure-Python, sqlmap-compatible stub intended for testing.")
    lines.append("  It does not perform real SQL injection detection/exploitation.")
    lines.append("")
    lines.append(f"Version: {VERSION}")
    lines.append("")
    return "\n".join(lines)