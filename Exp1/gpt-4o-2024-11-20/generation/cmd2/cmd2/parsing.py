# cmd2/parsing.py

"""
Utilities for argument and command parsing.
"""

import argparse


class ArgumentParser(argparse.ArgumentParser):
    """
    Custom ArgumentParser for Cmd2 commands.
    Overrides error handling to integrate with Cmd2's error reporting.
    """

    def error(self, message):
        raise ValueError(f"Argument parsing error: {message}")


class CommandParser:
    """
    A simple parser for command-line commands.
    """

    def __init__(self):
        self.parser = ArgumentParser()

    def add_argument(self, *args, **kwargs):
        self.parser.add_argument(*args, **kwargs)

    def parse_args(self, args):
        return self.parser.parse_args(args)


def parse_command_line(command_line):
    """
    Parse a command line string into arguments.
    """
    return command_line.split()