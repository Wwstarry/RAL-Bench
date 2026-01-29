"""
Python Markdown

A Python implementation of John Gruber's Markdown.

Documentation: https://python-markdown.github.io/
"""

from .core import Markdown, markdown, markdownFromFile

__all__ = ['Markdown', 'markdown', 'markdownFromFile']
__version__ = '3.0.0'