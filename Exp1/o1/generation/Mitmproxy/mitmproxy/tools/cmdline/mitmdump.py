"""
Minimal argument parsing for mitmdump.
"""

import argparse

def create_parser():
    """
    Creates the argument parser for the mitmdump command.
    """
    parser = argparse.ArgumentParser(
        prog="mitmdump",
        description="Minimal stub of mitmdump's command line interface."
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit."
    )
    return parser