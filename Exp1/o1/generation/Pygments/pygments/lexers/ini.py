"""
A minimal INI lexer.
"""

import re

from ..token import Text, Comment, Keyword, Name, Operator, String, Token
from ..util import option

class IniLexer:
    name = "INI"

    def __init__(self, **options):
        pass

    def get_tokens(self, text, **options):
        """
        Very naive INI parsing:
        - Comments start with # or ;
        - Sections: [Section]
        - key = value
        """

        for line in text.splitlines(True):
            stripped = line.strip()
            # check for comment
            if stripped.startswith(";") or stripped.startswith("#"):
                yield Comment, line
                continue
            # check for section
            if stripped.startswith("[") and stripped.endswith("]"):
                yield Keyword, line
                continue
            # parse key = value
            if "=" in line:
                prefix, value = line.split("=", 1)
                yield Name.Attribute, prefix
                yield Operator, "="
                yield String, value
            else:
                yield Text, line