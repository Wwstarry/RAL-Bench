"""
Formatter registry and convenience exports.
"""

from typing import Dict, Type

from pygments.util import ClassNotFound

__all__ = [
    "HtmlFormatter",
    "TerminalFormatter",
    "get_formatter_by_name",
]

from pygments.formatters.html import HtmlFormatter  # noqa: E402
from pygments.formatters.terminal import TerminalFormatter  # noqa: E402

_FORMATTERS: Dict[str, Type] = {
    "html": HtmlFormatter,
    "terminal": TerminalFormatter,
    "console": TerminalFormatter,
}


def get_formatter_by_name(name: str, **opts):
    try:
        cls = _FORMATTERS[name.lower()]
    except KeyError as exc:
        raise ClassNotFound(f"No formatter for alias {name!r}") from exc
    return cls(**opts)