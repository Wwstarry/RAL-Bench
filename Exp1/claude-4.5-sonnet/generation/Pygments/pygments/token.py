"""
Token types for syntax highlighting.
"""


class _TokenType(tuple):
    """
    A token type is represented as a tuple of strings.
    """
    
    def __new__(cls, *args):
        if args:
            return tuple.__new__(cls, args)
        return tuple.__new__(cls)
    
    def __init__(self, *args):
        self.subtypes = set()
    
    def __contains__(self, item):
        """Check if item is a subtype of this token."""
        return item[:len(self)] == self
    
    def __getattr__(self, name):
        """Create subtypes on the fly."""
        new = _TokenType(*(self + (name,)))
        setattr(self, name, new)
        self.subtypes.add(new)
        return new
    
    def __repr__(self):
        return 'Token' + ('.' + '.'.join(self) if self else '')
    
    def __str__(self):
        return '.'.join(self) if self else 'Token'


Token = _TokenType()

# Standard token types
Text = Token.Text
Whitespace = Text.Whitespace
Escape = Token.Escape
Error = Token.Error
Other = Token.Other

Keyword = Token.Keyword
Keyword.Constant = Token.Keyword.Constant
Keyword.Declaration = Token.Keyword.Declaration
Keyword.Namespace = Token.Keyword.Namespace
Keyword.Pseudo = Token.Keyword.Pseudo
Keyword.Reserved = Token.Keyword.Reserved
Keyword.Type = Token.Keyword.Type

Name = Token.Name
Name.Attribute = Token.Name.Attribute
Name.Builtin = Token.Name.Builtin
Name.Builtin.Pseudo = Token.Name.Builtin.Pseudo
Name.Class = Token.Name.Class
Name.Constant = Token.Name.Constant
Name.Decorator = Token.Name.Decorator
Name.Entity = Token.Name.Entity
Name.Exception = Token.Name.Exception
Name.Function = Token.Name.Function
Name.Function.Magic = Token.Name.Function.Magic
Name.Property = Token.Name.Property
Name.Label = Token.Name.Label
Name.Namespace = Token.Name.Namespace
Name.Other = Token.Name.Other
Name.Tag = Token.Name.Tag
Name.Variable = Token.Name.Variable
Name.Variable.Class = Token.Name.Variable.Class
Name.Variable.Global = Token.Name.Variable.Global
Name.Variable.Instance = Token.Name.Variable.Instance
Name.Variable.Magic = Token.Name.Variable.Magic

Literal = Token.Literal
Literal.Date = Token.Literal.Date

String = Literal.String
String.Affix = Token.Literal.String.Affix
String.Backtick = Token.Literal.String.Backtick
String.Char = Token.Literal.String.Char
String.Delimiter = Token.Literal.String.Delimiter
String.Doc = Token.Literal.String.Doc
String.Double = Token.Literal.String.Double
String.Escape = Token.Literal.String.Escape
String.Heredoc = Token.Literal.String.Heredoc
String.Interpol = Token.Literal.String.Interpol
String.Other = Token.Literal.String.Other
String.Regex = Token.Literal.String.Regex
String.Single = Token.Literal.String.Single
String.Symbol = Token.Literal.String.Symbol

Number = Literal.Number
Number.Bin = Token.Literal.Number.Bin
Number.Float = Token.Literal.Number.Float
Number.Hex = Token.Literal.Number.Hex
Number.Integer = Token.Literal.Number.Integer
Number.Integer.Long = Token.Literal.Number.Integer.Long
Number.Oct = Token.Literal.Number.Oct

Operator = Token.Operator
Operator.Word = Token.Operator.Word

Punctuation = Token.Punctuation
Punctuation.Marker = Token.Punctuation.Marker

Comment = Token.Comment
Comment.Hashbang = Token.Comment.Hashbang
Comment.Multiline = Token.Comment.Multiline
Comment.Preproc = Token.Comment.Preproc
Comment.PreprocFile = Token.Comment.PreprocFile
Comment.Single = Token.Comment.Single
Comment.Special = Token.Comment.Special

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


STANDARD_TYPES = {
    Token: '',
    Text: '',
    Whitespace: 'w',
    Escape: 'esc',
    Error: 'err',
    Other: 'x',
    
    Keyword: 'k',
    Keyword.Constant: 'kc',
    Keyword.Declaration: 'kd',
    Keyword.Namespace: 'kn',
    Keyword.Pseudo: 'kp',
    Keyword.Reserved: 'kr',
    Keyword.Type: 'kt',
    
    Name: 'n',
    Name.Attribute: 'na',
    Name.Builtin: 'nb',
    Name.Builtin.Pseudo: 'bp',
    Name.Class: 'nc',
    Name.Constant: 'no',
    Name.Decorator: 'nd',
    Name.Entity: 'ni',
    Name.Exception: 'ne',
    Name.Function: 'nf',
    Name.Function.Magic: 'fm',
    Name.Property: 'py',
    Name.Label: 'nl',
    Name.Namespace: 'nn',
    Name.Other: 'nx',
    Name.Tag: 'nt',
    Name.Variable: 'nv',
    Name.Variable.Class: 'vc',
    Name.Variable.Global: 'vg',
    Name.Variable.Instance: 'vi',
    Name.Variable.Magic: 'vm',
    
    Literal: 'l',
    Literal.Date: 'ld',
    
    String: 's',
    String.Affix: 'sa',
    String.Backtick: 'sb',
    String.Char: 'sc',
    String.Delimiter: 'dl',
    String.Doc: 'sd',
    String.Double: 's2',
    String.Escape: 'se',
    String.Heredoc: 'sh',
    String.Interpol: 'si',
    String.Other: 'sx',
    String.Regex: 'sr',
    String.Single: 's1',
    String.Symbol: 'ss',
    
    Number: 'm',
    Number.Bin: 'mb',
    Number.Float: 'mf',
    Number.Hex: 'mh',
    Number.Integer: 'mi',
    Number.Integer.Long: 'il',
    Number.Oct: 'mo',
    
    Operator: 'o',
    Operator.Word: 'ow',
    
    Punctuation: 'p',
    Punctuation.Marker: 'pm',
    
    Comment: 'c',
    Comment.Hashbang: 'ch',
    Comment.Multiline: 'cm',
    Comment.Preproc: 'cp',
    Comment.PreprocFile: 'cpf',
    Comment.Single: 'c1',
    Comment.Special: 'cs',
    
    Generic: 'g',
    Generic.Deleted: 'gd',
    Generic.Emph: 'ge',
    Generic.Error: 'gr',
    Generic.Heading: 'gh',
    Generic.Inserted: 'gi',
    Generic.Output: 'go',
    Generic.Prompt: 'gp',
    Generic.Strong: 'gs',
    Generic.Subheading: 'gu',
    Generic.Traceback: 'gt',
}


def is_token_subtype(ttype, other):
    """Check if ttype is a subtype of other."""
    if not isinstance(ttype, tuple):
        return False
    if not isinstance(other, tuple):
        return False
    return ttype[:len(other)] == other


def string_to_tokentype(s):
    """Convert a string like 'Token.Keyword.Reserved' to a token type."""
    if not s or s == 'Token':
        return Token
    parts = s.split('.')
    if parts[0] == 'Token':
        parts = parts[1:]
    node = Token
    for part in parts:
        node = getattr(node, part)
    return node