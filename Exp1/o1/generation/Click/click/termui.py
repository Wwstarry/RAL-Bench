# click/termui.py
# Utility functions for terminal-based user interaction including echo, secho, etc.

import sys

# Basic ANSI codes for color output.
_ANSI_RESET = "\033[0m"
_ANSI_COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    # Add more if needed
}

def echo(message=None, file=None, nl=True, err=False, color=None):
    """
    Prints a message to stdout (or the given file).
    If err=True, print to stderr.
    If nl=True, append a newline.
    color can be a string for a foreground color, or None for no color.
    """
    if file is None:
        file = sys.stderr if err else sys.stdout

    if message is None:
        message = ""

    out = message
    if color in _ANSI_COLORS:
        out = _ANSI_COLORS[color] + out + _ANSI_RESET

    if nl:
        print(out, file=file)
    else:
        print(out, file=file, end="")

def secho(message=None, file=None, nl=True, err=False, fg=None):
    """
    Like echo, but shorter color argument name "fg".
    """
    echo(message, file=file, nl=nl, err=err, color=fg)