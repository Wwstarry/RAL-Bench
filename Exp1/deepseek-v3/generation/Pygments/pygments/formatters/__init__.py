"""Formatter registry."""

import sys
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.terminal import TerminalFormatter

# Registry of available formatters
_formatter_cache = {}

def _load_formatters():
    """Load all available formatters."""
    formatters = [
        HtmlFormatter,
        TerminalFormatter,
    ]
    
    for formatter_class in formatters:
        _formatter_cache[formatter_class.name.lower()] = formatter_class
        for alias in getattr(formatter_class, 'aliases', []):
            _formatter_cache[alias.lower()] = formatter_class

def get_formatter_by_name(alias, **options):
    """Get a formatter by name or alias."""
    if not _formatter_cache:
        _load_formatters()
    
    alias_lower = alias.lower()
    if alias_lower in _formatter_cache:
        formatter_class = _formatter_cache[alias_lower]
        return formatter_class(**options)
    
    raise ClassNotFound(f"No formatter found for alias '{alias}'")

# Initialize on import
_load_formatters()