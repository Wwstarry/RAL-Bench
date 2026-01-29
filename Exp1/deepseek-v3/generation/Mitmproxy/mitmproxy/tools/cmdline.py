"""Command line argument parsing"""

import argparse
from typing import List

def mitmdump(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse mitmdump command line arguments"""
    parser = argparse.ArgumentParser(
        description="mitmdump - command-line version of mitmproxy",
        prog="mitmdump"
    )
    
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8080,
        help="Proxy service port"
    )
    
    parser.add_argument(
        "-b", "--bind-address",
        default="",
        help="Address to bind proxy to"
    )
    
    parser.add_argument(
        "--mode",
        choices=["regular", "transparent", "socks5", "reverse", "upstream"],
        default="regular",
        help="Proxy mode"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose"
    )
    
    parser.add_argument(
        "filters",
        nargs="*",
        help="Filter expressions"
    )
    
    return parser.parse_args(args)