"""
Pygments - Python syntax highlighter.
"""

__version__ = '1.0.0'
__all__ = ['lex', 'highlight', 'token', 'util']

from pygments.lex import lex
from pygments.highlight import highlight
import pygments.token
import pygments.util