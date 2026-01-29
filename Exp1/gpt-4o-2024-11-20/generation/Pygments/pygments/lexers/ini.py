from pygments.token import Token

class IniLexer:
    """
    A simple lexer for INI files.
    """
    def get_tokens(self, code):
        for line in code.splitlines():
            if line.startswith("[") and line.endswith("]"):
                yield Token.Name, line
            elif "=" in line:
                yield Token.Operator, line
            elif line.startswith(";"):
                yield Token.Comment, line
            else:
                yield Token.Text, line