"""
    pygments.filters
    ~~~~~~~~~~~~~~~~

    Pygments filters.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

# This is a placeholder as filter implementation is not required.

class Filter:
    """
    Base class for filters.
    """
    def __init__(self, **options):
        self.options = options

    def filter(self, lexer, stream):
        raise NotImplementedError