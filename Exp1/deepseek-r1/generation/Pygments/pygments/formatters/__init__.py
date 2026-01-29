"""
Formatter package.
"""

from pygments.formatters.html import HtmlFormatter
from pygments.formatters.terminal import TerminalFormatter

__all__ = ['HtmlFormatter', 'TerminalFormatter']

_formatter_cache = {}

def _load_formatters():
    """Load all formatters."""
    return {
        'html': HtmlFormatter,
        'terminal': TerminalFormatter,
    }

def get_formatter_by_name(name, **options):
    """Get formatter by name."""
    if not _formatter_cache:
        _formatter_cache.update(_load_formatters())
    
    name = name.lower()
    if name in _formatter_cache:
        return _formatter_cache[name](**options)
    raise ClassNotFound(f"No formatter for alias {name!r} found")