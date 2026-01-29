"""
Miscellaneous tiny utilities needed by the reduced pygments clone.
"""

__all__ = ["ClassNotFound"]


class ClassNotFound(ValueError):
    """
    Raised by :pyfunc:`pygments.lexers.get_lexer_by_name` when no suitable
    lexer is available for the requested language.
    """

    def __init__(self, message: str):
        super().__init__(message)