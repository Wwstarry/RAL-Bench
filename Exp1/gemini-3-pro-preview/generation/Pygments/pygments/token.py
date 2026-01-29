class _TokenType(tuple):
    parent = None

    def __getattr__(self, val):
        if not val or not val[0].isupper():
            return tuple.__getattribute__(self, val)
        new = _TokenType(self + (val,))
        new.parent = self
        return new

    def __repr__(self):
        return 'Token' + ('.' if self else '') + '.'.join(self)

    def __str__(self):
        return 'Token' + ('.' if self else '') + '.'.join(self)

Token = _TokenType()

# Standard Token Types
Text = Token.Text
Whitespace = Token.Text.Whitespace
Error = Token.Error
Other = Token.Other

Keyword = Token.Keyword
Name = Token.Name
Literal = Token.Literal
String = Token.Literal.String
Number = Token.Literal.Number
Operator = Token.Operator
Punctuation = Token.Punctuation
Comment = Token.Comment
Generic = Token.Generic

# Common Subtypes
Keyword.Constant = Keyword.Constant
Keyword.Declaration = Keyword.Declaration
Keyword.Namespace = Keyword.Namespace
Keyword.Pseudo = Keyword.Pseudo
Keyword.Reserved = Keyword.Reserved
Keyword.Type = Keyword.Type

Name.Attribute = Name.Attribute
Name.Builtin = Name.Builtin
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

Number.Bin = Number.Bin
Number.Float = Number.Float
Number.Hex = Number.Hex
Number.Integer = Number.Integer
Number.Oct = Number.Oct

Operator.Word = Operator.Word

Comment.Hashbang = Comment.Hashbang
Comment.Multiline = Comment.Multiline
Comment.Preproc = Comment.Preproc
Comment.Single = Comment.Single
Comment.Special = Comment.Special

STANDARD_TYPES = {
    Token: '',
    Text: '',
    Whitespace: 'w',
    Error: 'err',
    Other: 'x',
    Keyword: 'k',
    Name: 'n',
    Literal: 'l',
    String: 's',
    Number: 'm',
    Operator: 'o',
    Punctuation: 'p',
    Comment: 'c',
    Generic: 'g',
}