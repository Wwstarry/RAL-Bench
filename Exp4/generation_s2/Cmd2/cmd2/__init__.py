"""
Lightweight, pure-Python subset of the cmd2 project.

This package provides enough API compatibility for educational use and for
black-box tests expecting core cmd2 behaviors.
"""

from .cmd2 import Cmd2, Cmd2ArgumentParser, Statement, Cmd2Error
from . import parsing, utils

__all__ = [
    "Cmd2",
    "Cmd2ArgumentParser",
    "Statement",
    "Cmd2Error",
    "parsing",
    "utils",
]