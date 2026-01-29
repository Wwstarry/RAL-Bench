"""
Pure Python CLI framework compatible with Click API.
"""

from .core import (
    BaseCommand,
    Command,
    Group,
    Context,
    Parameter,
    Option,
    Argument,
    MultiCommand,
    CommandCollection,
)
from .decorators import (
    command,
    group,
    option,
    argument,
    pass_context,
    make_pass_decorator,
)
from .utils import (
    echo,
    secho,
    get_binary_stream,
    get_text_stream,
    open_file,
    format_filename,
    get_app_dir,
    get_os_args,
)
from .termui import (
    prompt,
    confirm,
    get_terminal_size,
    clear,
    style,
    unstyle,
    getchar,
    pause,
    edit,
    launch,
    get_current_terminal,
    progressbar,
)
from .testing import CliRunner, Result

__all__ = [
    # Core classes
    "BaseCommand",
    "Command",
    "Group",
    "Context",
    "Parameter",
    "Option",
    "Argument",
    "MultiCommand",
    "CommandCollection",
    
    # Decorators
    "command",
    "group",
    "option",
    "argument",
    "pass_context",
    "make_pass_decorator",
    
    # Utilities
    "echo",
    "secho",
    "get_binary_stream",
    "get_text_stream",
    "open_file",
    "format_filename",
    "get_app_dir",
    "get_os_args",
    
    # TermUI
    "prompt",
    "confirm",
    "get_terminal_size",
    "clear",
    "style",
    "unstyle",
    "getchar",
    "pause",
    "edit",
    "launch",
    "get_current_terminal",
    "progressbar",
    
    # Testing
    "CliRunner",
    "Result",
]

# Shortcut decorators
click = _ClickNamespace()

class _ClickNamespace:
    """Namespace object for decorator shortcuts."""
    
    def __getattr__(self, name):
        if name == "command":
            return command
        elif name == "group":
            return group
        elif name == "option":
            return option
        elif name == "argument":
            return argument
        elif name == "pass_context":
            return pass_context
        else:
            raise AttributeError(f"module 'click' has no attribute '{name}'")