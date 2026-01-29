from .console import Console
from .table import Table
from .progress import Progress, track
from .text import Text
from .theme import Theme

_console = Console()

def print(*objects, sep=" ", end="\n", style=None, justify=None):
    _console.print(*objects, sep=sep, end=end, style=style, justify=justify)

def inspect(obj, console=None):
    c = console or _console
    c.print(obj)