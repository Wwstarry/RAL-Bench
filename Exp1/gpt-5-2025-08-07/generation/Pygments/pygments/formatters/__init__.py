from ..util import ClassNotFound
from .html import HtmlFormatter
from .terminal import TerminalFormatter

_formatter_by_name = {
    "html": HtmlFormatter,
    "htm": HtmlFormatter,
    "terminal": TerminalFormatter,
    "ansi": TerminalFormatter,
}

def get_formatter_by_name(name, **options):
    cls = _formatter_by_name.get(name.lower())
    if not cls:
        raise ClassNotFound(f"No formatter for name '{name}'")
    return cls(**options)