"""
Lexer for Python source code.
"""

import re
from pygments.lex import RegexLexer, bygroups, include
from pygments.token import (
    Text, Comment, Operator, Keyword, Name, String,
    Number, Punctuation, Error, Whitespace
)


class PythonLexer(RegexLexer):
    """
    Lexer for Python source code.
    """
    
    name = 'Python'
    aliases = ['python', 'py']
    filenames = ['*.py', '*.pyw']
    mimetypes = ['text/x-python', 'application/x-python']
    
    flags = re.MULTILINE | re.UNICODE
    
    tokens = {
        'root': [
            (re.compile(r'\n'), Whitespace, None),
            (re.compile(r'\s+'), Whitespace, None),
            (re.compile(r'#.*$'), Comment.Single, None),
            (re.compile(r'"""'), String.Doc, 'tdqs'),
            (re.compile(r"'''"), String.Doc, 'tsqs'),
            (re.compile(r'"'), String.Double, 'dqs'),
            (re.compile(r"'"), String.Single, 'sqs'),
            
            # Keywords
            (re.compile(r'\b(False|None|True)\b'), Keyword.Constant, None),
            (re.compile(r'\b(and|as|assert|async|await|break|class|continue|'
                       r'def|del|elif|else|except|finally|for|from|global|'
                       r'if|import|in|is|lambda|nonlocal|not|or|pass|raise|'
                       r'return|try|while|with|yield)\b'), Keyword, None),
            
            # Builtins
            (re.compile(r'\b(__import__|abs|all|any|bin|bool|bytearray|bytes|'
                       r'chr|classmethod|compile|complex|delattr|dict|dir|'
                       r'divmod|enumerate|eval|filter|float|format|frozenset|'
                       r'getattr|globals|hasattr|hash|hex|id|input|int|'
                       r'isinstance|issubclass|iter|len|list|locals|map|max|'
                       r'memoryview|min|next|object|oct|open|ord|pow|print|'
                       r'property|range|repr|reversed|round|set|setattr|'
                       r'slice|sorted|staticmethod|str|sum|super|tuple|type|'
                       r'vars|zip)\b'), Name.Builtin, None),
            
            # Magic methods and attributes
            (re.compile(r'\b__[a-zA-Z_][a-zA-Z0-9_]*__\b'), Name.Function.Magic, None),
            
            # Decorators
            (re.compile(r'@[a-zA-Z_][a-zA-Z0-9_]*'), Name.Decorator, None),
            
            # Numbers
            (re.compile(r'0[bB][01]+'), Number.Bin, None),
            (re.compile(r'0[oO][0-7]+'), Number.Oct, None),
            (re.compile(r'0[xX][0-9a-fA-F]+'), Number.Hex, None),
            (re.compile(r'\d+\.\d+([eE][+-]?\d+)?'), Number.Float, None),
            (re.compile(r'\d+[eE][+-]?\d+'), Number.Float, None),
            (re.compile(r'\d+'), Number.Integer, None),
            
            # Operators
            (re.compile(r'[+\-*/%&|^~<>=!]=?'), Operator, None),
            (re.compile(r'\*\*|//|<<|>>'), Operator, None),
            
            # Punctuation
            (re.compile(r'[()[\]{}:;,.]'), Punctuation, None),
            
            # Names
            (re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*'), Name, None),
        ],
        'dqs': [
            (re.compile(r'\\[\\"]'), String.Escape, None),
            (re.compile(r'[^"\\]+'), String.Double, None),
            (re.compile(r'"'), String.Double, '#pop'),
        ],
        'sqs': [
            (re.compile(r"\\[\\']"), String.Escape, None),
            (re.compile(r"[^'\\]+"), String.Single, None),
            (re.compile(r"'"), String.Single, '#pop'),
        ],
        'tdqs': [
            (re.compile(r'"""'), String.Doc, '#pop'),
            (re.compile(r'[^"\\]+'), String.Doc, None),
            (re.compile(r'"'), String.Doc, None),
            (re.compile(r'\\.'), String.Escape, None),
        ],
        'tsqs': [
            (re.compile(r"'''"), String.Doc, '#pop'),
            (re.compile(r"[^'\\]+"), String.Doc, None),
            (re.compile(r"'"), String.Doc, None),
            (re.compile(r'\\.'), String.Escape, None),
        ],
    }
    
    def analyse_text(text):
        """Check if text looks like Python code."""
        score = 0.0
        if re.search(r'\bdef\s+\w+\s*\(', text):
            score += 0.1
        if re.search(r'\bclass\s+\w+\s*[:(]', text):
            score += 0.1
        if re.search(r'\bimport\s+\w+', text):
            score += 0.1
        if re.search(r'\bfrom\s+\w+\s+import\b', text):
            score += 0.1
        return min(score, 1.0)