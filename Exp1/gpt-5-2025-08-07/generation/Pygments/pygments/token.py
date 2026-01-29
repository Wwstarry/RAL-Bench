# Minimal Token type hierarchy compatible enough with Pygments

class TokenType:
    __slots__ = ("_name", "_parent", "_children")

    def __init__(self, name, parent=None):
        self._name = name
        self._parent = parent
        self._children = {}

    def __getattr__(self, item):
        # create children lazily
        child_name = f"{self._name}.{item}"
        child = self._children.get(item)
        if child is None:
            child = TokenType(child_name, self)
            self._children[item] = child
        return child

    def __repr__(self):
        return f"<TokenType {self._name}>"

    def __str__(self):
        return self._name

    def parent(self):
        return self._parent

    def split(self):
        # returns tuple path of names (without "Token" root)
        if self._parent is None:
            return ()
        pieces = []
        cur = self
        while cur is not None and cur._parent is not None:
            pieces.append(cur._name.split(".")[-1])
            cur = cur._parent
        return tuple(reversed(pieces))

    def is_child_of(self, other):
        cur = self
        while cur is not None:
            if cur is other:
                return True
            cur = cur._parent
        return False

    def __contains__(self, ttype):
        # allow 'ttype in Token.String'
        if not isinstance(ttype, TokenType):
            return False
        return ttype.is_child_of(self)

# Root token
Token = TokenType("Token")

# Common token types hierarchy (subset sufficient for tests)
Text = Token.Text
Whitespace = Token.Whitespace
Error = Token.Error
Other = Token.Other

Keyword = Token.Keyword
Name = Token.Name
Literal = Token.Literal
String = Token.String
Number = Token.Number

Operator = Token.Operator
Punctuation = Token.Punctuation
Comment = Token.Comment
Generic = Token.Generic

# Subtypes often used
Keyword.Constant = Keyword.Constant
Keyword.Declaration = Keyword.Declaration
Keyword.Namespace = Keyword.Namespace
Keyword.Reserved = Keyword.Reserved
Keyword.Type = Keyword.Type

Name.Attribute = Name.Attribute
Name.Builtin = Name.Builtin
Name.Class = Name.Class
Name.Constant = Name.Constant
Name.Decorator = Name.Decorator
Name.Exception = Name.Exception
Name.Function = Name.Function
Name.Label = Name.Label
Name.Namespace = Name.Namespace
Name.Tag = Name.Tag
Name.Variable = Name.Variable

Literal.Date = Literal.Date

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

Number.Float = Number.Float
Number.Hex = Number.Hex
Number.Integer = Number.Integer
Number.Oct = Number.Oct

Operator.Word = Operator.Word

Punctuation.Marker = Punctuation.Marker

Comment.Multiline = Comment.Multiline
Comment.Preproc = Comment.Preproc
Comment.Single = Comment.Single
Comment.Special = Comment.Special

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

# Helper functions

def is_token_subtype(ttype, parent):
    """
    Return True if ttype is a subtype of parent.
    """
    if not isinstance(ttype, TokenType) or not isinstance(parent, TokenType):
        return False
    return ttype.is_child_of(parent)

# Map top-level token groups to short CSS class codes, similar to Pygments
STANDARD_TYPES = {
    Comment: "c",
    Keyword: "k",
    Name: "n",
    Literal: "l",
    String: "s",
    Number: "m",
    Operator: "o",
    Punctuation: "p",
    Generic: "g",
    Whitespace: "w",
    Text: "t",
    Error: "err",
}

def token_to_css_class(ttype):
    """
    Resolve a token type to a CSS class short name.

    We map top-level groups to single-letter classes similar to the reference.
    """
    # Walk parents to find a mapped group
    cur = ttype
    while cur is not None:
        if cur in STANDARD_TYPES:
            base = STANDARD_TYPES[cur]
            # try to extend with subtype suffix, e.g., Name.Function -> nf
            if cur is Name:
                # append first letter of subtype if present
                parts = ttype.split()
                if parts:
                    code = parts[0]
                    if code:
                        return "n" + code[0].lower()
            if cur is String:
                parts = ttype.split()
                if parts:
                    return "s" + parts[0][0].lower()
            if cur is Keyword:
                parts = ttype.split()
                if parts:
                    return "k" + parts[0][0].lower()
            return base
        cur = cur.parent()
    # default to 't'
    return "t"