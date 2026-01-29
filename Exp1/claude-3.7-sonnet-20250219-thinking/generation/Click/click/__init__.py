# -*- coding: utf-8 -*-
"""
    click
    ~~~~~

    A simple command line interface toolkit.
"""

from .core import Context, Command, Group, Argument, Option, Parameter
from .decorators import command, group, argument, option
from .termui import echo, secho, prompt, confirm
from .utils import get_text_stream

__version__ = '0.1.0'
__all__ = [
    'Context', 'Command', 'Group', 'Argument', 'Option', 'Parameter',
    'command', 'group', 'argument', 'option',
    'echo', 'secho', 'prompt', 'confirm',
    'get_text_stream'
]