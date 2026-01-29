from pygments.util import ClassNotFound
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.terminal import TerminalFormatter

_FORMATTER_REGISTRY = {
    'html': HtmlFormatter,
    'terminal': TerminalFormatter,
    'console': TerminalFormatter,
}

def get_formatter_by_name(_alias, **options):
    cls = _FORMATTER_REGISTRY.get(_alias.lower())
    if cls:
        return cls(**options)
    raise ClassNotFound("No formatter found for name %r" % _alias)

__all__ = ['get_formatter_by_name', 'HtmlFormatter', 'TerminalFormatter']