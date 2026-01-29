"""
Lightweight compatibility layer for the core API of the cmd2 project.

This package provides a simplified pure-Python command-line application framework
that mimics the core behavior of cmd2 sufficiently for black-box tests, including:

- The Cmd2 class (subclassing cmd.Cmd)
- Parsing utilities for arguments and options
- Output capture and transcript-based testing support
- Help generation and tab-completion hooks integration via cmd.Cmd conventions
"""

from .cmd2 import Cmd2, TranscriptError
from .parsing import Statement, parse_command, join_arg_list, unquote
from .utils import StdSim, strip_quotes, quote_string

__all__ = [
    "Cmd2",
    "TranscriptError",
    "Statement",
    "parse_command",
    "join_arg_list",
    "unquote",
    "StdSim",
    "strip_quotes",
    "quote_string",
]

# Provide a version string for compatibility checks if present in tests
__version__ = "0.0.1"