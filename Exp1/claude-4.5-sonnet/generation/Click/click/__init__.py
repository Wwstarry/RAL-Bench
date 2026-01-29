"""
Click - A pure Python CLI framework compatible with the reference Click project.
"""

from .core import (
    Context,
    Command,
    Group,
    Parameter,
    Option,
    Argument,
)
from .decorators import (
    command,
    group,
    option,
    argument,
    pass_context,
)
from .termui import (
    echo,
    secho,
    prompt,
    confirm,
    style,
)
from .testing import CliRunner
from .exceptions import (
    ClickException,
    UsageError,
    BadParameter,
    Abort,
)

__version__ = "8.0.0"

__all__ = [
    "Context",
    "Command",
    "Group",
    "Parameter",
    "Option",
    "Argument",
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
    "ClickException",
    "UsageError",
    "BadParameter",
    "Abort",
]