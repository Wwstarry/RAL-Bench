"""
Click - A Python package for creating command line interfaces.
"""

from click.core import (
    Context,
    Command,
    Group,
    Option,
    Argument,
    Parameter,
)
from click.decorators import (
    command,
    group,
    option,
    argument,
    pass_context,
)
from click.termui import (
    echo,
    secho,
    prompt,
    confirm,
    style,
)
from click.testing import CliRunner

__version__ = "8.0.0"

__all__ = [
    "Context",
    "Command",
    "Group",
    "Option",
    "Argument",
    "Parameter",
    "command",
    "group",
    "option",
    "argument",
    "pass_context",
    "echo",
    "secho",
    "prompt",
    "confirm",
    "style",
    "CliRunner",
]