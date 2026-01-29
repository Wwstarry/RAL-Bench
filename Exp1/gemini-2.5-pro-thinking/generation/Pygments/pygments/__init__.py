"""
pygments
~~~~~~~~

Pygments is a syntax highlighting package written in Python.

This is a pure-Python implementation designed to be API-compatible
with the core parts of the reference Pygments project.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

__version__ = '2.10.0'
__docformat__ = 'restructuredtext'

from pygments.lex import lex
from pygments.highlight import highlight

__all__ = ['highlight', 'lex']