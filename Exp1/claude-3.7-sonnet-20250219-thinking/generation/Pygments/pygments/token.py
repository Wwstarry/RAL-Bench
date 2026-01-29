# -*- coding: utf-8 -*-
"""
    pygments.token
    ~~~~~~~~~~~~~

    Basic token types and the standard tokens.

    :copyright: Copyright 2006-2023 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

__all__ = ['Token', 'Text', 'Whitespace', 'Escape', 'Error', 'Other', 'Keyword',
           'Name', 'Literal', 'String', 'Number', 'Punctuation', 'Operator',
           'Comment', 'Generic', 'is_token_subtype']


class _TokenType(tuple):
    """
    A token type and its parent types.

    Type hierarchies are encoded by having a nested tuple structure. For
    instance, `String.Double` has the parent types `String` and `Token`.
    """
    parent = None

    def __init__(self, *args):
        # no need to call super().__init__
        self.subtypes = {}

    def __contains__(self, val):
        """
        Return True if ``val`` is a subtype of ``self``.
        """
        if self == val:
            return True
        return any(isinstance(typ, _TokenType) and val in typ
                   for typ in self.subtypes.values())

    def __getattr__(self, name):
        if name == 'subtypes':
            raise AttributeError()
        if name not in self.subtypes:
            new_type = _TokenType(self + (name,))
            new_type.parent = self
            self.subtypes[name] = new_type
        return self.subtypes[name]

    def __repr__(self):
        return 'Token' + ('' if self == () else '.' + '.'.join(self))


Token = _TokenType()

# Special token types
Text = Token.Text
Whitespace = Text.Whitespace
Escape = Token.Escape
Error = Token.Error
Other = Token.Other

# Common token types
Keyword = Token.Keyword
Name = Token.Name
Literal = Token.Literal
String = Literal.String
Number = Literal.Number
Punctuation = Token.Punctuation
Operator = Token.Operator
Comment = Token.Comment
Generic = Token.Generic


def is_token_subtype(ttype, other):
    """
    Return True if ``ttype`` is a subtype of ``other``.
    """
    while ttype is not None:
        if ttype == other:
            return True
        ttype = ttype.parent
    return False