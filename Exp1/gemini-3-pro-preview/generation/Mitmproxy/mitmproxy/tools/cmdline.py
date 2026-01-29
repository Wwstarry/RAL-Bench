import argparse

def mitmdump() -> argparse.ArgumentParser:
    """
    Returns the argument parser for mitmdump.
    """
    parser = argparse.ArgumentParser(description="mitmdump")
    
    # Basic arguments expected by tests/users
    parser.add_argument(
        "--version",
        action="store_true",
        help="show version number and exit"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Increase verbosity."
    )
    parser.add_argument(
        "-s", "--scripts",
        action="append",
        help="Execute a script."
    )
    parser.add_argument(
        "-p", "--listen-port",
        type=int,
        dest="listen_port",
        help="Proxy service port."
    )
    parser.add_argument(
        "--mode",
        dest="mode",
        help="Mode of operation (regular, transparent, socks5, etc)."
    )
    
    return parser