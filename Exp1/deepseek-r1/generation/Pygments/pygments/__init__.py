"""
Pygments - Python syntax highlighter.
"""

__version__ = '2.0.0'
__all__ = ['lex', 'highlight', 'token', 'util', 'lexers', 'formatters', 'styles', 'filters']

from pygments.lex import lex
from pygments.highlight import highlight
from pygments import token
from pygments import util
from pygments import lexers
from pygments import formatters
from pygments import styles
from pygments import filters