"""
Token types for syntax highlighting.
"""


class _TokenType:
    """Represents a token type in the highlighting system."""
    
    def __init__(self, parent=None, name=''):
        self.parent = parent
        self.name = name
        self._subtypes = {}
    
    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(f"Token has no attribute {name}")
        if name not in self._subtypes:
            self._subtypes[name] = _TokenType(self, name)
        return self._subtypes[name]
    
    def __repr__(self):
        if self.parent is None:
            return 'Token'
        parts = []
        current = self
        while current.parent is not None:
            parts.append(current.name)
            current = current.parent
        return 'Token.' + '.'.join(reversed(parts))
    
    def __str__(self):
        return repr(self)
    
    def __eq__(self, other):
        if isinstance(other, _TokenType):
            return repr(self) == repr(other)
        return False
    
    def __hash__(self):
        return hash(repr(self))
    
    def is_subtype_of(self, other):
        """Check if this token is a subtype of another."""
        current = self
        while current is not None:
            if current == other:
                return True
            current = current.parent
        return False


# Root token type
Token = _TokenType()

# Common token types
Text = Token.Text
Whitespace = Token.Text.Whitespace
Error = Token.Error
Comment = Token.Comment
Operator = Token.Operator
Keyword = Token.Keyword
Name = Token.Name
String = Token.String
Number = Token.Number
Literal = Token.Literal
Punctuation = Token.Punctuation

# Subtypes
Comment.Single = Token.Comment.Single
Comment.Multiline = Token.Comment.Multiline
Comment.Special = Token.Comment.Special

Keyword.Constant = Token.Keyword.Constant
Keyword.Declaration = Token.Keyword.Declaration
Keyword.Namespace = Token.Keyword.Namespace
Keyword.Pseudo = Token.Keyword.Pseudo
Keyword.Reserved = Token.Keyword.Reserved
Keyword.Type = Token.Keyword.Type

Name.Attribute = Token.Name.Attribute
Name.Builtin = Token.Name.Builtin
Name.Class = Token.Name.Class
Name.Constant = Token.Name.Constant
Name.Decorator = Token.Name.Decorator
Name.Entity = Token.Name.Entity
Name.Exception = Token.Name.Exception
Name.Function = Token.Name.Function
Name.Label = Token.Name.Label
Name.Namespace = Token.Name.Namespace
Name.Other = Token.Name.Other
Name.Tag = Token.Name.Tag
Name.Variable = Token.Name.Variable

String.Affix = Token.String.Affix
String.Backtick = Token.String.Backtick
String.Char = Token.String.Char
String.Delimiter = Token.String.Delimiter
String.Doc = Token.String.Doc
String.Double = Token.String.Double
String.Escape = Token.String.Escape
String.Heredoc = Token.String.Heredoc
String.Interpol = Token.String.Interpol
String.Other = Token.String.Other
String.Regex = Token.String.Regex
String.Single = Token.String.Single
String.Symbol = Token.String.Symbol

Number.Bin = Token.Number.Bin
Number.Float = Token.Number.Float
Number.Hex = Token.Number.Hex
Number.Integer = Token.Number.Integer
Number.Oct = Token.Number.Oct

Literal.Date = Token.Literal.Date

Punctuation.Marker = Token.Punctuation.Marker

Generic = Token.Generic
Generic.Deleted = Token.Generic.Deleted
Generic.Emph = Token.Generic.Emph
Generic.Error = Token.Generic.Error
Generic.Heading = Token.Generic.Heading
Generic.Inserted = Token.Generic.Inserted
Generic.Output = Token.Generic.Output
Generic.Prompt = Token.Generic.Prompt
Generic.Strong = Token.Generic.Strong
Generic.Subheading = Token.Generic.Subheading
Generic.Traceback = Token.Generic.Traceback
</file:

<file:name=pygments/util.py>
"""
Utility functions for Pygments.
"""

import re


def get_bool_opt(options, name, default=False):
    """Get a boolean option from a dictionary."""
    value = options.get(name, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)


def get_int_opt(options, name, default=0):
    """Get an integer option from a dictionary."""
    value = options.get(name, default)
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def get_list_opt(options, name, default=None):
    """Get a list option from a dictionary."""
    if default is None:
        default = []
    value = options.get(name, default)
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [x.strip() for x in value.split(',')]
    return default


def docstring_heading(text):
    """Format a docstring heading."""
    return text


class ClassNotFound(Exception):
    """Exception raised when a class cannot be found."""
    pass