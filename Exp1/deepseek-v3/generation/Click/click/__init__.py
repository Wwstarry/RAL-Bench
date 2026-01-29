"""
Click - A simple Python package for creating beautiful command line interfaces.
"""

from .core import (
    BaseCommand,
    Command,
    Context,
    Group,
    MultiCommand,
    Option,
    Parameter,
    CommandCollection,
)
from .decorators import (
    command,
    group,
    option,
    argument,
    pass_context,
    pass_obj,
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
    style,
    unstyle,
    clear,
    edit,
    launch,
    getchar,
    pause,
    progressbar,
)

# Core public API
__all__ = [
    # Core classes
    'BaseCommand',
    'Command',
    'Context',
    'Group',
    'MultiCommand',
    'Option',
    'Parameter',
    'CommandCollection',
    
    # Decorators
    'command',
    'group',
    'option',
    'argument',
    'pass_context',
    'pass_obj',
    'make_pass_decorator',
    
    # Utilities
    'echo',
    'secho',
    'get_binary_stream',
    'get_text_stream',
    'open_file',
    'format_filename',
    'get_app_dir',
    'get_os_args',
    
    # Terminal UI
    'prompt',
    'confirm',
    'style',
    'unstyle',
    'clear',
    'edit',
    'launch',
    'getchar',
    'pause',
    'progressbar',
]

# Version
__version__ = '8.1.0'