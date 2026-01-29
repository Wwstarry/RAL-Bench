"""
Pure Python interactive command-line application framework.

This package provides a framework for building interactive command-line
applications with features like command registration, tab completion,
help generation, and transcript-based testing.
"""

__version__ = '0.1.0'
__all__ = [
    'Cmd2',
    'Statement',
    'ParsedString',
    'CommandResult',
    'Transcript',
    'with_argparser',
    'with_argument_list',
    'with_default_category',
    'with_category',
    'as_subcommand_to',
    'history',
    'output',
    'utils',
]

from .cmd2 import Cmd2
from .parsing import Statement, ParsedString
from .utils import CommandResult, Transcript
from .decorators import (
    with_argparser,
    with_argument_list,
    with_default_category,
    with_category,
    as_subcommand_to,
)
from . import history
from . import output
from . import utils