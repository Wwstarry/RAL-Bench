import argparse


def mitmdump_args_parser():
    parser = argparse.ArgumentParser(
        prog="mitmdump",
        description="A minimal mitmdump CLI argument parser"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=8080,
        help="Port to listen on"
    )
    parser.add_argument(
        "-s", "--script", type=str, default=None,
        help="Load a script"
    )
    parser.add_argument(
        "--version", action="version", version="mitmdump 1.0"
    )
    return parser


def parse_args(args=None):
    parser = mitmdump_args_parser()
    return parser.parse_args(args)