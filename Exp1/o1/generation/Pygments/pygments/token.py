"""
Defines token types and utilities for Pygments-like tokens.
"""

class TokenType(str):
    """
    Simple string-based token type for minimal compatibility.
    """

    def split(self):
        return self.splittext()

    def splittext(self):
        return self.rsplit('.', 1)

def is_token_subtype(ttype, other):
    """
    Check if ttype is a subtype of other.
    """
    if ttype == other:
        return True
    if not ttype or not other:
        return False
    parts1 = ttype.split('.')
    parts2 = other.split('.')
    if len(parts1) < len(parts2):
        return False
    return parts1[:len(parts2)] == parts2

Token = TokenType("Token")

# Common token names for Pygments
Text = TokenType("Token.Text")
Whitespace = TokenType("Token.Text.Whitespace")
Error = TokenType("Token.Error")
Other = TokenType("Token.Other")

Keyword = TokenType("Token.Keyword")
KeywordConstant = TokenType("Token.Keyword.Constant")
KeywordDeclaration = TokenType("Token.Keyword.Declaration")
KeywordNamespace = TokenType("Token.Keyword.Namespace")
KeywordPseudo = TokenType("Token.Keyword.Pseudo")
KeywordReserved = TokenType("Token.Keyword.Reserved")
KeywordType = TokenType("Token.Keyword.Type")

Name = TokenType("Token.Name")
NameBuiltin = TokenType("Token.Name.Builtin")
NameFunction = TokenType("Token.Name.Function")
NameClass = TokenType("Token.Name.Class")
NameNamespace = TokenType("Token.Name.Namespace")
NameException = TokenType("Token.Name.Exception")
NameVariable = TokenType("Token.Name.Variable")
NameConstant = TokenType("Token.Name.Constant")
NameLabel = TokenType("Token.Name.Label")
NameEntity = TokenType("Token.Name.Entity")
NameAttribute = TokenType("Token.Name.Attribute")
NameTag = TokenType("Token.Name.Tag")
NameDecorator = TokenType("Token.Name.Decorator")

Literal = TokenType("Token.Literal")
String = TokenType("Token.Literal.String")
StringDoc = TokenType("Token.Literal.String.Doc")
StringInterpol = TokenType("Token.Literal.String.Interpol")
StringEscape = TokenType("Token.Literal.String.Escape")
StringRegex = TokenType("Token.Literal.String.Regex")
StringSymbol = TokenType("Token.Literal.String.Symbol")
StringBinary = TokenType("Token.Literal.String.Binary")
StringCharacter = TokenType("Token.Literal.String.Char")
StringOther = TokenType("Token.Literal.String.Other")
Number = TokenType("Token.Literal.Number")
NumberInteger = TokenType("Token.Literal.Number.Integer")
NumberFloat = TokenType("Token.Literal.Number.Float")
NumberOct = TokenType("Token.Literal.Number.Oct")
NumberHex = TokenType("Token.Literal.Number.Hex")
NumberBin = TokenType("Token.Literal.Number.Bin")
NumberComplex = TokenType("Token.Literal.Number.Complex")

Operator = TokenType("Token.Operator")
OperatorWord = TokenType("Token.Operator.Word")

Punctuation = TokenType("Token.Punctuation")

Comment = TokenType("Token.Comment")
CommentMultiline = TokenType("Token.Comment.Multiline")
CommentSingle = TokenType("Token.Comment.Single")
CommentSpecial = TokenType("Token.Comment.Special")