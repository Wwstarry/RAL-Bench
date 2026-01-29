import argparse

def mitmdump():
    """
    Creates and returns the argparse parser for mitmdump.
    This is used to validate CLI argument stability and help output.
    """
    parser = argparse.ArgumentParser(
        prog="mitmdump",
        description="A minimal, safe-to-evaluate subset of mitmdump.",
        add_help=False,
    )

    # Add a subset of common mitmdump arguments to match the API surface
    # exercised by the test suite.

    group = parser.add_argument_group("Mitmproxy")
    group.add_argument(
        "-h", "--help",
        action="help",
        help="show this help message and exit"
    )
    group.add_argument(
        "--version",
        action="store_true",
        dest="show_version",
        help="show version number and exit"
    )
    group.add_argument(
        "-q", "--quiet",
        action="store_true",
        dest="quiet",
        help="Quiet mode."
    )
    group.add_argument(
        "-s", "--scripts",
        dest="scripts",
        nargs="+",
        default=[],
        metavar="SCRIPT",
        help="Execute a script."
    )

    group = parser.add_argument_group("Proxy Options")
    group.add_argument(
        "-p", "--listen-port",
        dest="listen_port",
        type=int,
        default=8080,
        metavar="PORT",
        help="Proxy listen port."
    )
    group.add_argument(
        "--mode",
        dest="mode",
        type=str,
        default="regular",
        help="Proxy mode."
    )
    group.add_argument(
        "--set",
        dest="set",
        nargs='*',
        default=[],
        metavar="OPTION=VALUE",
        help="Set a mitmproxy option."
    )

    return parser