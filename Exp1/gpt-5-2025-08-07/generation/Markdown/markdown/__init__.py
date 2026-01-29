"""
A minimal pure-Python Markdown-to-HTML conversion library exposing a public API
compatible with core parts of the reference Python-Markdown project.

Public API:
- markdown.markdown(text, **kwargs)
- markdown.markdownFromFile(**kwargs)
- markdown.Markdown class with convert(text) and reset()
"""

from .core import Markdown, markdown, markdownFromFile

__all__ = ["Markdown", "markdown", "markdownFromFile"]

# Minimal version identifier
__version__ = "0.1.0"