"""
    pygments.token
    ~~~~~~~~~~~~~~

    Definitions for token types.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

class _TokenType(tuple):
    """
    Represents a token type.
    Created by cascading attribute access on the `Token` class.
    """
    parent = None

    def __getattr__(self, name):
        if name[0].islower():
            raise AttributeError("token type names must be capitalized")
        new = _TokenType(self + (name,))
        new.parent = self
        return new

    def __repr__(self):
        return 'Token' + ('.' if self else '') + '.'.join(self)


Token = _TokenType()

# Standard token types
Text = Token.Text
Whitespace = Text.Whitespace

Comment = Token.Comment
Comment.Single = Comment.Single
Comment.Multiline = Comment.Multiline
Comment.Special = Comment.Special
Comment.Preproc = Comment.Preproc

Keyword = Token.Keyword
Keyword.Constant = Keyword.Constant
Keyword.Declaration = Keyword.Declaration
Keyword.Namespace = Keyword.Namespace
Keyword.Pseudo = Keyword.Pseudo
Keyword.Reserved = Keyword.Reserved
Keyword.Type = Keyword.Type

Operator = Token.Operator
Operator.Word = Operator.Word

Name = Token.Name
Name.Attribute = Name.Attribute
Name.Builtin = Name.Builtin
Name.Builtin.Pseudo = Name.Builtin.Pseudo
Name.Class = Name.Class
Name.Constant = Name.Constant
Name.Decorator = Name.Decorator
Name.Entity = Name.Entity
Name.Exception = Name.Exception
Name.Function = Name.Function
Name.Label = Name.Label
Name.Namespace = Name.Namespace
Name.Other = Name.Other
Name.Tag = Name.Tag
Name.Variable = Name.Variable

Literal = Token.Literal
Literal.Date = Literal.Date

String = Literal.String
String.Backtick = String.Backtick
String.Char = String.Char
String.Doc = String.Doc
String.Double = String.Double
String.Escape = String.Escape
String.Heredoc = String.Heredoc
String.Interpol = String.Interpol
String.Other = String.Other
String.Regex = String.Regex
String.Single = String.Single
String.Symbol = String.Symbol

Number = Literal.Number
Number.Float = Number.Float
Number.Hex = Number.Hex
Number.Integer = Number.Integer
Number.Integer.Long = Number.Integer.Long
Number.Oct = Number.Oct

Punctuation = Token.Punctuation

Generic = Token.Generic
Generic.Deleted = Generic.Deleted
Generic.Emph = Generic.Emph
Generic.Error = Generic.Error
Generic.Heading = Generic.Heading
Generic.Inserted = Generic.Inserted
Generic.Output = Generic.Output
Generic.Prompt = Generic.Prompt
Generic.Strong = Generic.Strong
Generic.Subheading = Generic.Subheading
Generic.Traceback = Generic.Traceback

Error = Token.Error

# Helper functions
def is_token_subtype(ttype, other):
    """
    Return ``True`` if `ttype` is a subtype of `other`.
    """
    return ttype is other or (
        isinstance(ttype, tuple) and
        len(ttype) > len(other) and
        ttype[:len(other)] == other
    )

def string_to_tokentype(s):
    """
    Convert a string like ``'Token.Literal.String'`` to the corresponding
    token type object.
    """
    if not s:
        return Token
    if not s.startswith('Token'):
        raise ValueError("string must start with 'Token'")
    s = s[5:]
    if not s:
        return Token
    obj = Token
    for part in s.split('.'):
        if not part: continue
        obj = getattr(obj, part)
    return obj