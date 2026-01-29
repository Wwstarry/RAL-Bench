"""
cmd2 - A pure Python interactive command-line application framework
API-compatible with core parts of the reference Cmd2 project
"""

from .cmd2 import Cmd
from .parsing import Statement
from .utils import redirect_output

__version__ = '2.0.0'
__all__ = ['Cmd', 'Statement', 'redirect_output']

# Expose Cmd as Cmd2 for compatibility
Cmd2 = Cmd