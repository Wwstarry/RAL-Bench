"""
Formatter registry and lookup functions.
"""

from pygments.util import ClassNotFound


def get_formatter_by_name(name, **options):
    """
    Get a formatter by its short name.
    
    Args:
        name: Short name of the formatter (e.g., 'html', 'terminal')
        **options: Options to pass to the formatter
        
    Returns:
        Formatter instance
        
    Raises:
        ClassNotFound: If no formatter with that name exists
    """
    name = name.lower()
    
    if name == 'html':
        from pygments.formatters.html import HtmlFormatter
        return HtmlFormatter(**options)
    elif name in ('terminal', 'console'):
        from pygments.formatters.terminal import TerminalFormatter
        return TerminalFormatter(**options)
    else:
        raise ClassNotFound(f'No formatter found for name {name!r}')


def get_all_formatters():
    """
    Return a generator of all available formatters.
    
    Yields:
        Formatter classes
    """
    from pygments.formatters.html import HtmlFormatter
    from pygments.formatters.terminal import TerminalFormatter
    
    yield HtmlFormatter
    yield TerminalFormatter