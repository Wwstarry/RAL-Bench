import argparse

def create_parser() -> argparse.ArgumentParser:
    """
    Creates the argparse.ArgumentParser instance for mitmdump.
    This is used by the main entry point to parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        prog="mitmdump",
        description="A minimal, safe-to-evaluate subset of mitmdump.",
        add_help=False,  # We handle help manually for compatibility.
    )
    # Standard options
    generic = parser.add_argument_group("Generic Options")
    generic.add_argument(
        '--version', action='store_true',
        help="Show version number and exit."
    )
    generic.add_argument(
        '-h', '--help', action='store_true',
        help="Show this help message and exit."
    )
    generic.add_argument(
        '-q', '--quiet', action='store_true',
        help="Quiet mode."
    )
    generic.add_argument(
        '-v', '--verbose', action='store_true',
        help="Increase verbosity."
    )

    # Scripting options
    scripting = parser.add_argument_group("Scripting")
    scripting.add_argument(
        '-s', '--scripts', dest="scripts", nargs='+',
        help="Execute a script."
    )

    # Flow I/O
    flow_io = parser.add_argument_group("Flow Input/Output")
    flow_io.add_argument(
        '-r', '--rfile', dest="rfile",
        help="Read flows from a file."
    )
    flow_io.add_argument(
        '-w', '--wfile', dest="wfile",
        help="Write flows to a file."
    )

    # Proxy options
    proxy = parser.add_argument_group("Proxy Options")
    proxy.add_argument(
        '-p', '--listen-port', type=int, dest="listen_port", default=8080,
        help="Proxy listen port."
    )
    proxy.add_argument(
        '--mode', dest="mode",
        help="Proxy mode."
    )
    return parser