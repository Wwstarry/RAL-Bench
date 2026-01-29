from __future__ import annotations

from typing import Dict, Optional


class TokenType:
    """
    Hierarchical token type node, similar to Pygments' TokenType.

    Instances form a tree:
      Token.Name.Function is a distinct singleton child of Token.Name.

    Subtype checks:
      Token.Name.Function in Token.Name   -> True
      Token.Name in Token.Name.Function   -> False
    """

    __slots__ = ("_parent", "_name", "_children")

    def __init__(self, parent: Optional["TokenType"] = None, name: str = ""):
        self._parent = parent
        self._name = name
        self._children: Dict[str, TokenType] = {}

    @property
    def parent(self) -> Optional["TokenType"]:
        return self._parent

    @property
    def subtypes(self) -> Dict[str, "TokenType"]:
        return self._children

    def __getattr__(self, item: str) -> "TokenType":
        if item.startswith("_"):
            raise AttributeError(item)
        child = self._children.get(item)
        if child is None:
            child = TokenType(self, item)
            self._children[item] = child
        return child

    def __contains__(self, other: "TokenType") -> bool:
        """
        True if 'other' is this token or a subtype of this token.
        """
        t = other
        while t is not None:
            if t is self:
                return True
            t = t.parent
        return False

    def split(self):
        parts = []
        t = self
        while t is not None and t._name:
            parts.append(t._name)
            t = t.parent
        return tuple(reversed(parts))

    def __repr__(self) -> str:
        if self._parent is None and self._name == "":
            return "Token"
        parts = self.split()
        return "Token." + ".".join(parts)

    __str__ = __repr__


def is_token_subtype(ttype: TokenType, other: TokenType) -> bool:
    return other.__contains__(ttype)


Token = TokenType(None, "")

Text = Token.Text
Whitespace = Text.Whitespace

Error = Token.Error
Other = Token.Other

Keyword = Token.Keyword
Name = Token.Name
Literal = Token.Literal
String = Literal.String
Number = Literal.Number
Operator = Token.Operator
Punctuation = Token.Punctuation
Comment = Token.Comment
Generic = Token.Generic

# Common subtypes (subset)
Keyword.Constant
Keyword.Declaration
Keyword.Namespace
Keyword.Pseudo
Keyword.Reserved
Keyword.Type

Name.Builtin
Name.Function
Name.Class
Name.Decorator
Name.Namespace
Name.Attribute
Name.Tag
Name.Variable
Name.Constant

String.Single
String.Double
String.Doc
String.Escape

Number.Integer
Number.Float

Operator.Word

Comment.Single
Comment.Multiline

Generic.Heading
Generic.Subheading
Generic.Deleted
Generic.Inserted
Generic.Error