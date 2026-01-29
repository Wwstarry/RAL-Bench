# Minimal Click-compatible public API shim

from .core import (
    Context,
    Command,
    Group,
    ClickException,
    UsageError,
    BadParameter,
    MissingParameter,
)
from .decorators import command, group, option, argument, pass_context
from .termui import echo, secho
from . import testing
from . import utils
from . import termui

__all__ = [
    "Context",
    "Command",
    "Group",
    "ClickException",
    "UsageError",
    "BadParameter",
    "MissingParameter",
    "command",
    "group",
    "option",
    "argument",
    "pass_context",
    "echo",
    "secho",
    "testing",
    "utils",
    "termui",
]