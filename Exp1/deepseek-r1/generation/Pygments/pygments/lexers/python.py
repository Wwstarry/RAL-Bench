"""
Python lexer.
"""

import re
from pygments.lexer import RegexLexer
from pygments.token import Token

__all__ = ['PythonLexer']

class PythonLexer(RegexLexer):
    """Lexer for Python code."""
    
    name = 'Python'
    aliases = ['python', 'py']
    filenames = ['*.py']
    
    tokens = {
        'root': [
            (r'\n', Token.Text),
            (r'^#.*$', Token.Comment.Single),
            (r'""".*?"""', Token.Comment.Multiline),
            (r"'''.*?'''", Token.Comment.Multiline),
            (r'#.*$', Token.Comment.Single),
            (r'[\t ]+', Token.Text.Whitespace),
            (r'\\\n', Token.Text.Whitespace),
            (r'\\', Token.Text),
            (r'\b(and|as|assert|break|class|continue|def|del|elif|else|'
             r'except|exec|finally|for|from|global|if|import|in|is|lambda|'
             r'not|or|pass|print|raise|return|try|while|with|yield)\b',
             Token.Keyword),
            (r'\b(True|False|None)\b', Token.Keyword.Constant),
            (r'\b(self|cls)\b', Token.Name.Builtin.Pseudo),
            (r'\b[+-]?[0-9]+\b', Token.Literal.Number.Integer),
            (r'\b[+-]?[0-9]*\.[0-9]+\b', Token.Literal.Number.Float),
            (r'"[^"]*"', Token.Literal.String.Double),
            (r"'[^']*'", Token.Literal.String.Single),
            (r'[a-zA-Z_][a-zA-Z0-9_]*', Token.Name),
            (r'[(){}\[\],:.]', Token.Punctuation),
            (r'[=+\-*/%&|^~<>!]', Token.Operator),
            (r'.', Token.Text),
        ]
    }