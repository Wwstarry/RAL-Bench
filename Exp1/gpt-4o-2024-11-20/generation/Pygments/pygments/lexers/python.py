from pygments.token import Token

class PythonLexer:
    """
    A simple lexer for Python code.
    """
    def get_tokens(self, code):
        for line in code.splitlines():
            if line.startswith("#"):
                yield Token.Comment, line
            elif line.startswith(" "):
                yield Token.Whitespace, line
            elif line.startswith(("def", "class")):
                yield Token.Keyword, line
            else:
                yield Token.Text, line