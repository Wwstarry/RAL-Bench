"""
Formatters for Pygments output.
"""

from pygments.util import ClassNotFound


def get_formatter_by_name(name, **options):
    """Get a formatter by its name."""
    name_lower = name.lower()
    
    if name_lower in ('html',):
        from pygments.formatters.html import HtmlFormatter
        return HtmlFormatter(**options)
    elif name_lower in ('terminal', 'ansi'):
        from pygments.formatters.terminal import TerminalFormatter
        return TerminalFormatter(**options)
    else:
        raise ClassNotFound(f"No formatter found for name {name!r}")


__all__ = ['get_formatter_by_name']