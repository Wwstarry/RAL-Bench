"""
Formatter package.
"""

from pygments.formatters.html import HtmlFormatter
from pygments.formatters.terminal import TerminalFormatter

def get_formatter_by_name(name, **options):
    """Get a formatter by its name."""
    formatters = {
        'html': HtmlFormatter,
        'terminal': TerminalFormatter,
        'terminal256': TerminalFormatter,
    }
    
    if name in formatters:
        return formatters[name](**options)
    raise ValueError(f"Unknown formatter: {name}")