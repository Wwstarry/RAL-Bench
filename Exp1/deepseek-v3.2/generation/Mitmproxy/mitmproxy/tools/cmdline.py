"""
Command line argument parsing for mitmproxy tools.
"""

import argparse
import sys
from typing import List, Optional, Any


class ArgumentParser(argparse.ArgumentParser):
    """Custom argument parser for mitmproxy."""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('add_help', False)
        super().__init__(*args, **kwargs)
    
    def error(self, message: str) -> None:
        """Handle parse errors."""
        sys.stderr.write(f'error: {message}\n')
        self.print_help()
        sys.exit(2)


def mitmdump(args: Optional[List[str]] = None) -> Any:
    """
    Parse mitmdump command line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = ArgumentParser(
        prog="mitmdump",
        description="An interactive, SSL/TLS-capable intercepting proxy.",
        epilog="See mitmproxy.io for more information and documentation."
    )
    
    # Basic options
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8080,
        help="Proxy service port (default: 8080)"
    )
    parser.add_argument(
        "-b", "--bind-address",
        default="",
        help="Address to bind proxy to (default: all interfaces)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Increase log verbosity"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit"
    )
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show this help message and exit"
    )
    
    # Parse arguments
    if args is None:
        args = sys.argv[1:]
    
    return parser.parse_args(args)


def print_help() -> None:
    """Print help for mitmdump."""
    parser = ArgumentParser(
        prog="mitmdump",
        description="An interactive, SSL/TLS-capable intercepting proxy.",
        epilog="See mitmproxy.io for more information and documentation."
    )
    
    # Add all arguments
    mitmdump([])
    parser.print_help()