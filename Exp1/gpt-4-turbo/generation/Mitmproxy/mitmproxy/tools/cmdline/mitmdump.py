# Minimal mitmproxy.tools.cmdline.mitmdump argument specification/parsing

import argparse

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="mitmdump",
        description="Minimal mitmdump CLI"
    )
    parser.add_argument(
        "-r", "--read-flows",
        help="Read flows from file"
    )
    parser.add_argument(
        "-w", "--write-flows",
        help="Write flows to file"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="mitmdump 0.0.1"
    )
    return parser.parse_args(argv)