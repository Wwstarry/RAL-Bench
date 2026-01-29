# click/utils.py

import sys


def echo(message=None, file=None, nl=True):
    file = file or sys.stdout
    if message:
        file.write(message)
    if nl:
        file.write("\n")


def secho(message=None, file=None, nl=True, fg=None, bg=None, bold=None):
    # For simplicity, we ignore color handling in this implementation.
    echo(message, file=file, nl=nl)