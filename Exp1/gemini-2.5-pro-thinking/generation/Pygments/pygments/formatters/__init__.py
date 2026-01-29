"""
    pygments.formatters
    ~~~~~~~~~~~~~~~~~~~

    Pygments formatters.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from pygments.util import ClassNotFound
from pygments.styles import get_style_by_name

__all__ = ['get_formatter_by_name', 'Formatter']

_FORMATTERS = {}

def _import_formatters():
    """Dynamically import all formatters."""
    from . import html, terminal
    for formatter_cls in [html.HtmlFormatter, terminal.TerminalFormatter]:
        for alias in formatter_cls.aliases:
            _FORMATTERS[alias] = formatter_cls
_import_formatters()


def get_formatter_by_name(alias, **options):
    """
    Get a formatter by an alias.
    Raises ClassNotFound if no formatter is found.
    """
    if alias.lower() in _FORMATTERS:
        return _FORMATTERS[alias.lower()](**options)
    raise ClassNotFound(f"No formatter found for alias '{alias}'")


class Formatter:
    """
    Converts a token stream to text.
    """
    name = None
    aliases = []
    filenames = []

    def __init__(self, **options):
        self.options = options
        self.style = self._get_style(options)

    def _get_style(self, options):
        style = options.get('style', 'default')
        if isinstance(style, str):
            return get_style_by_name(style)
        return style

    def get_style_defs(self, arg=''):
        """
        Return CSS style definitions for the current style.
        `arg` is an additional selector.
        """
        return ''

    def format(self, tokensource, outfile):
        """
        Format `tokensource`, an iterable of `(tokentype, tokenstring)`
        tuples and write it to `outfile`.
        """
        raise NotImplementedError