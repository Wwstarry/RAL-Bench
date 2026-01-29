# click/__init__.py
# Top-level click package initialization.

__version__ = "0.1"

# Re-export key functionalities for convenience.
from .core import Context, Command, Group
from .decorators import command, group, option, argument
from .termui import echo, secho
from .testing import CliRunner

__all__ = [
    "Context",
    "Command",
    "Group",
    "command",
    "group",
    "option",
    "argument",
    "echo",
    "secho",
    "CliRunner",
    "__version__",
]