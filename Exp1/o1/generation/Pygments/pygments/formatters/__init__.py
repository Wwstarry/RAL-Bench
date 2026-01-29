"""
Base formatter definitions and get_formatter_by_name function.
"""

from ..util import ClassNotFound

class Formatter:
    """
    Minimal base class for formatters.
    """
    def __init__(self, **options):
        pass

    def format(self, tokensource, outfile):
        """
        Must be implemented by subclasses.
        """
        raise NotImplementedError()

_formatters_by_name = {}

def get_formatter_by_name(name, **options):
    """
    Return a formatter instance for the given `name`.
    """
    name = name.lower()
    if name in _formatters_by_name:
        return _formatters_by_name[name](**options)
    raise ClassNotFound("No formatter for name %r found." % name)