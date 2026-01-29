"""
Command line argument parsing for mitmproxy tools.
"""

import argparse
from typing import Optional


def mitmdump() -> argparse.ArgumentParser:
    """
    Create and return argument parser for mitmdump.
    
    Returns:
        ArgumentParser configured for mitmdump
    """
    parser = argparse.ArgumentParser(
        prog="mitmdump",
        description="An interactive TLS-capable intercepting proxy",
        add_help=True
    )
    
    # Core options
    parser.add_argument(
        "-l", "--listen-host",
        default="127.0.0.1",
        help="Address to listen on (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "-p", "--listen-port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)"
    )
    
    parser.add_argument(
        "-m", "--mode",
        default="regular",
        choices=["regular", "transparent", "socks5", "reverse", "upstream"],
        help="Proxy mode (default: regular)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress output"
    )
    
    parser.add_argument(
        "-d", "--flow-detail",
        type=int,
        default=2,
        choices=[0, 1, 2, 3],
        help="Flow detail level (0-3, default: 2)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="mitmdump 10.0.0"
    )
    
    parser.add_argument(
        "-s", "--script",
        action="append",
        dest="scripts",
        help="Load a Python script as an addon"
    )
    
    parser.add_argument(
        "-c", "--cert",
        help="Path to certificate file"
    )
    
    parser.add_argument(
        "-k", "--key",
        help="Path to key file"
    )
    
    parser.add_argument(
        "--no-server",
        action="store_true",
        help="Don't start a proxy server"
    )
    
    return parser