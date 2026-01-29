from __future__ import annotations

from pygments.util import ClassNotFound

from .html import HtmlFormatter
from .terminal import TerminalFormatter

_FORMATTERS = {
    "html": HtmlFormatter,
    "terminal": TerminalFormatter,
    "ansi": TerminalFormatter,
}

def get_formatter_by_name(name: str, **options):
    if not name:
        raise ClassNotFound(name)
    cls = _FORMATTERS.get(name.lower().strip())
    if cls is None:
        raise ClassNotFound(name)
    return cls(**options)

__all__ = ["HtmlFormatter", "TerminalFormatter", "get_formatter_by_name"]