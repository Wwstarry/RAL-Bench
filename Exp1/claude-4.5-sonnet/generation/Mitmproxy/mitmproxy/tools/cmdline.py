"""
Command-line argument parsing for mitmproxy tools.
"""

import argparse
from typing import Optional, List


def mitmdump() -> argparse.ArgumentParser:
    """
    Create argument parser for mitmdump.
    """
    parser = argparse.ArgumentParser(
        prog="mitmdump",
        description="mitmdump is the command-line companion to mitmproxy. "
                    "It provides tcpdump-like functionality to let you view, "
                    "record, and programmatically transform HTTP traffic."
    )
    
    # Server options
    parser.add_argument(
        "--listen-host",
        type=str,
        default="127.0.0.1",
        help="Address to bind proxy to (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--listen-port", "-p",
        type=int,
        default=8080,
        help="Proxy service port (default: 8080)"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        action="append",
        help="Mode can be regular, transparent, socks5, reverse:SPEC, or upstream:SPEC"
    )
    
    # SSL options
    parser.add_argument(
        "--ssl-insecure",
        action="store_true",
        help="Do not verify upstream server SSL/TLS certificates"
    )
    
    parser.add_argument(
        "--cert",
        action="append",
        dest="certs",
        help="Add a certificate for interception"
    )
    
    # Flow options
    parser.add_argument(
        "--showhost",
        action="store_true",
        help="Use the Host header to construct URLs for display"
    )
    
    # Filter options
    parser.add_argument(
        "filter",
        nargs="?",
        help="Flow filter expression"
    )
    
    # Output options
    parser.add_argument(
        "-w", "--save-stream-file",
        type=str,
        help="Stream flows to file as they arrive"
    )
    
    # Script options
    parser.add_argument(
        "-s", "--scripts",
        action="append",
        help="Execute a script"
    )
    
    # Verbosity
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        dest="verbosity",
        help="Increase verbosity"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode"
    )
    
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit"
    )
    
    return parser


def mitmproxy() -> argparse.ArgumentParser:
    """
    Create argument parser for mitmproxy (console UI).
    """
    parser = argparse.ArgumentParser(
        prog="mitmproxy",
        description="mitmproxy is an interactive, SSL/TLS-capable intercepting proxy "
                    "with a console interface."
    )
    
    # Reuse common options from mitmdump
    dump_parser = mitmdump()
    
    # Copy arguments from mitmdump parser
    for action in dump_parser._actions:
        if action.dest != 'help':
            parser._add_action(action)
    
    return parser


def mitmweb() -> argparse.ArgumentParser:
    """
    Create argument parser for mitmweb (web UI).
    """
    parser = argparse.ArgumentParser(
        prog="mitmweb",
        description="mitmweb is a web-based interface for mitmproxy."
    )
    
    # Reuse common options from mitmdump
    dump_parser = mitmdump()
    
    # Copy arguments from mitmdump parser
    for action in dump_parser._actions:
        if action.dest != 'help':
            parser._add_action(action)
    
    # Add web-specific options
    parser.add_argument(
        "--web-host",
        type=str,
        default="127.0.0.1",
        help="Web interface host (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--web-port",
        type=int,
        default=8081,
        help="Web interface port (default: 8081)"
    )
    
    return parser