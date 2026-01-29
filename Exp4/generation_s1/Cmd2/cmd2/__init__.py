"""
Lightweight, pure-Python compatibility subset of the cmd2 project.

This package provides the minimal public API needed by the agent tests and
common black-box tests: Cmd2, parsing utilities, output capture, and transcript
testing support.
"""

from .cmd2 import Cmd2, Cmd2ArgumentParser
from .exceptions import Cmd2ArgparseError, CommandError
from .parsing import Statement, parse_statement, tokenize, shlex_split, quote_string_if_needed
from .transcript import TranscriptRunner, TranscriptResult, run_transcript_tests
from .utils import (
    strip_ansi,
    ensure_str,
    redirect_std,
    capture_std,
    capture_output,
)

__all__ = [
    "Cmd2",
    "Cmd2ArgumentParser",
    "Cmd2ArgparseError",
    "CommandError",
    "Statement",
    "parse_statement",
    "tokenize",
    "shlex_split",
    "quote_string_if_needed",
    "TranscriptRunner",
    "TranscriptResult",
    "run_transcript_tests",
    "strip_ansi",
    "ensure_str",
    "redirect_std",
    "capture_std",
    "capture_output",
]

__version__ = "0.0.test"