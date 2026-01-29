"""
Lexer package.
"""

import re
from pygments.lex import RegexLexer
from pygments.token import Token

class PythonLexer(RegexLexer):
    """Lexer for Python source code."""
    
    name = 'Python'
    aliases = ['python', 'py']
    filenames = ['*.py']
    
    tokens = {
        'root': [
            (r'\s+', Token.Text),
            (r'#.*$', Token.Comment.Single),
            (r'"""(?:.|\n)*?"""', Token.Comment.Multiline),
            (r"'''(?:.|\n)*?'''", Token.Comment.Multiline),
            (r'"(?:[^"\\]|\\.)*"', Token.Literal.String.Double),
            (r"'(?:[^'\\]|\\.)*'", Token.Literal.String.Single),
            (r'\b(and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b', Token.Keyword),
            (r'\b(True|False|None)\b', Token.Keyword.Constant),
            (r'\b(self|cls)\b', Token.Name.Builtin.Pseudo),
            (r'\b[0-9]+\b', Token.Literal.Number.Integer),
            (r'\b[0-9]+\.[0-9]+\b', Token.Literal.Number.Float),
            (r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', Token.Name),
            (r'[+\-*/%=&|^~<>!]', Token.Operator),
            (r'[\[\]{}():.,;]', Token.Punctuation),
        ]
    }

class JsonLexer(RegexLexer):
    """Lexer for JSON data."""
    
    name = 'JSON'
    aliases = ['json']
    filenames = ['*.json']
    
    tokens = {
        'root': [
            (r'\s+', Token.Text),
            (r'"(?:[^"\\]|\\.)*"', Token.Literal.String.Double),
            (r'\b(true|false|null)\b', Token.Keyword.Constant),
            (r'\b[0-9]+\b', Token.Literal.Number.Integer),
            (r'\b[0-9]+\.[0-9]+\b', Token.Literal.Number.Float),
            (r'[\[\]{}:,]', Token.Punctuation),
        ]
    }

class IniLexer(RegexLexer):
    """Lexer for INI files."""
    
    name = 'INI'
    aliases = ['ini', 'cfg']
    filenames = ['*.ini', '*.cfg']
    
    tokens = {
        'root': [
            (r'\s+', Token.Text),
            (r'[;#].*$', Token.Comment.Single),
            (r'\[.*?\]', Token.Name.Tag),
            (r'.*?=', Token.Name.Property),
            (r'.*$', Token.Literal.String),
        ]
    }

def get_lexer_by_name(name, **options):
    """Get a lexer by its name or alias."""
    lexers = {
        'python': PythonLexer,
        'py': PythonLexer,
        'json': JsonLexer,
        'ini': IniLexer,
        'cfg': IniLexer,
    }
    
    if name in lexers:
        return lexers[name](**options)
    raise ValueError(f"Unknown lexer: {name}")

def get_all_lexers():
    """Return a list of all lexers."""
    return [
        ('Python', ('python', 'py'), ('*.py',), ('text/x-python',)),
        ('JSON', ('json',), ('*.json',), ('application/json',)),
        ('INI', ('ini', 'cfg'), ('*.ini', '*.cfg'), ()),
    ]