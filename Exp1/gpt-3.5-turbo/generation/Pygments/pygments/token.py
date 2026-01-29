# Token types and helper functions

class _TokenType(tuple):
    def __new__(cls, name, parent=None):
        if parent is None:
            obj = tuple.__new__(cls, (name,))
        else:
            obj = tuple.__new__(cls, parent + (name,))
        obj._name = name
        obj._parent = parent
        return obj

    def __repr__(self):
        return 'Token.' + '.'.join(self)

    def __str__(self):
        return repr(self)

    def __getattr__(self, name):
        return _TokenType(name, self)

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        if isinstance(other, _TokenType):
            return tuple.__eq__(self, other)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

# Base token
Token = _TokenType('Token')

# Common token types
Text = Token.Text
Whitespace = Token.Whitespace
Error = Token.Error
Other = Token.Other

Keyword = Token.Keyword
Keyword.Constant = Keyword.Constant
Keyword.Declaration = Keyword.Declaration
Keyword.Namespace = Keyword.Namespace
Keyword.Pseudo = Keyword.Pseudo
Keyword.Reserved = Keyword.Reserved
Keyword.Type = Keyword.Type

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
Name.Variable.Class = Name.Variable.Class
Name.Variable.Global = Name.Variable.Global
Name.Variable.Instance = Name.Variable.Instance

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
Number.Bin = Number.Bin
Number.Float = Number.Float
Number.Hex = Number.Hex
Number.Integer = Number.Integer
Number.Integer.Long = Number.Integer.Long
Number.Oct = Number.Oct

Operator = Token.Operator
Operator.Word = Operator.Word

Punctuation = Token.Punctuation

Comment = Token.Comment
Comment.Multiline = Comment.Multiline
Comment.Preproc = Comment.Preproc
Comment.Single = Comment.Single
Comment.Special = Comment.Special

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

def is_token_subtype(t1, t2):
    # Check if t1 is a subtype of t2
    if not isinstance(t1, _TokenType) or not isinstance(t2, _TokenType):
        return False
    if len(t1) < len(t2):
        return False
    return t1[:len(t2)] == t2