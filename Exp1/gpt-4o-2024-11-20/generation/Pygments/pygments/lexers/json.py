from pygments.token import Token

class JsonLexer:
    """
    A simple lexer for JSON code.
    """
    def get_tokens(self, code):
        for char in code:
            if char in "{},:[]":
                yield Token.Punctuation, char
            elif char in "\"'":
                yield Token.String, char
            elif char.isdigit():
                yield Token.Number, char
            elif char.isspace():
                yield Token.Whitespace, char
            else:
                yield Token.Text, char