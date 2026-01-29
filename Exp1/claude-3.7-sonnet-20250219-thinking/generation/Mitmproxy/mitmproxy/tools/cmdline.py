"""
Command-line parsing for mitmproxy tools.
"""
import argparse
import sys
from typing import Sequence, Optional


def common_options(parser):
    """
    Add common options to the parser.
    """
    group = parser.add_argument_group("Common Options")
    group.add_argument(
        "--version", action="version", version="mitmproxy 10.0.0"
    )
    group.add_argument(
        "--options",
        action="store_true", dest="options",
        help="Show all options and their default values",
    )
    group.add_argument(
        "--commands",
        action="store_true", dest="commands",
        help="Show all commands and their signatures",
    )
    group.add_argument(
        "-v", "--verbose",
        action="count", dest="verbose", default=0,
        help="Increase verbosity (may be passed multiple times)"
    )


def mitmdump(args=None):
    """
    Parse arguments for mitmdump.
    """
    parser = argparse.ArgumentParser(usage="%(prog)s [options] [filter]")
    common_options(parser)
    
    group = parser.add_argument_group("Proxy Options")
    group.add_argument(
        "-p", "--listen-port",
        action="store", type=int, dest="listen_port", default=8080,
        help="Proxy service port"
    )
    group.add_argument(
        "-n", "--no-server",
        action="store_true", dest="no_server",
        help="Don't start a proxy server."
    )
    
    return parser.parse_args(args)


def mitmproxy(args=None):
    """
    Parse arguments for mitmproxy.
    """
    parser = argparse.ArgumentParser(usage="%(prog)s [options] [filter]")
    common_options(parser)
    
    group = parser.add_argument_group("Proxy Options")
    group.add_argument(
        "-p", "--listen-port",
        action="store", type=int, dest="listen_port", default=8080,
        help="Proxy service port"
    )
    
    return parser.parse_args(args)


def mitmweb(args=None):
    """
    Parse arguments for mitmweb.
    """
    parser = argparse.ArgumentParser(usage="%(prog)s [options] [filter]")
    common_options(parser)
    
    group = parser.add_argument_group("Web Interface Options")
    group.add_argument(
        "-p", "--listen-port",
        action="store", type=int, dest="listen_port", default=8080,
        help="Proxy service port"
    )
    group.add_argument(
        "--web-port",
        action="store", type=int, dest="web_port", default=8081,
        help="Web interface port"
    )
    group.add_argument(
        "--web-open-browser",
        action="store_true", dest="web_open_browser",
        help="Open web browser automatically"
    )
    
    return parser.parse_args(args)