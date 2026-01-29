# -*- coding: utf-8 -*-
#
# Copyright (c), 2024, All rights reserved.
#
"""
A pure Python implementation of a command-line application framework,
API-compatible with the core features of cmd2.
"""

__version__ = "1.0.0"

# Core classes and exceptions from the main module
from .cmd2 import (
    Cmd2,
    CommandResult,
    Statement,
    EmptyStatement,
    Cmd2ArgparseError,
    Cmd2ShlexError,
    SkipPostcommandHooks,
)

# Decorators for command parsing
from .parsing import (
    with_argparser,
    with_argparser_and_unknown_args,
    with_statement_parser,
)

# Utilities, especially for completion
from .utils import CompletionItem

# Alias Cmd to Cmd2 for compatibility with the standard library's cmd and older cmd2 usage
Cmd = Cmd2

# Define the public API of the package
__all__ = [
    # Core classes
    'Cmd',
    'Cmd2',
    'Statement',
    'EmptyStatement',
    'CommandResult',

    # Parsing decorators
    'with_argparser',
    'with_argparser_and_unknown_args',
    'with_statement_parser',

    # Utilities
    'CompletionItem',

    # Exceptions
    'Cmd2ArgparseError',
    'Cmd2ShlexError',
    'SkipPostcommandHooks',
]