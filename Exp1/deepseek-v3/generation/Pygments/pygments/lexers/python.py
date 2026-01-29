"""Python lexer implementation."""

import re
from pygments.lexer import RegexLexer
from pygments.token import Token

class PythonLexer(RegexLexer):
    """Lexer for Python source code."""
    
    name = 'Python'
    aliases = ['python', 'py']
    filenames = ['*.py']
    mimetypes = ['text/x-python']
    
    flags = re.MULTILINE | re.UNICODE
    
    tokens = {
        'root': [
            (r'\n', Token.Text),
            (r'^(\s*)(#.*?)$', bygroups(Token.Text, Token.Comment.Single)),
            (r'[^\S\n]+', Token.Text),
            
            # Keywords
            (r'\b(and|as|assert|break|class|continue|def|del|elif|else|'
             r'except|exec|finally|for|from|global|if|import|in|is|lambda|'
             r'not|or|pass|print|raise|return|try|while|with|yield)\b', 
             Token.Keyword),
             
            # Builtins
            (r'\b(ArithmeticError|AssertionError|AttributeError|BaseException|'
             r'BufferError|BytesWarning|DeprecationWarning|EOFError|'
             r'Ellipsis|EnvironmentError|Exception|False|FloatingPointError|'
             r'FutureWarning|GeneratorExit|IOError|ImportError|ImportWarning|'
             r'IndentationError|IndexError|KeyError|KeyboardInterrupt|'
             r'LookupError|MemoryError|NameError|None|NotImplemented|'
             r'NotImplementedError|OSError|OverflowError|PendingDeprecationWarning|'
             r'ReferenceError|RuntimeError|RuntimeWarning|StandardError|'
             r'StopIteration|SyntaxError|SyntaxWarning|SystemError|'
             r'SystemExit|TabError|True|TypeError|UnboundLocalError|'
             r'UnicodeDecodeError|UnicodeEncodeError|UnicodeError|'
             r'UnicodeTranslateError|UnicodeWarning|UserWarning|ValueError|'
             r'Warning|ZeroDivisionError|__import__|abs|all|any|apply|'
             r'basestring|bin|bool|buffer|bytearray|bytes|callable|chr|'
             r'classmethod|cmp|coerce|compile|complex|copyright|credits|'
             r'delattr|dict|dir|divmod|enumerate|eval|execfile|exit|file|'
             r'filter|float|format|frozenset|getattr|globals|hasattr|hash|'
             r'help|hex|id|input|int|intern|isinstance|issubclass|iter|'
             r'len|license|list|locals|long|map|max|memoryview|min|next|'
             r'object|oct|open|ord|pow|property|range|raw_input|reduce|'
             r'reload|repr|reversed|round|set|setattr|slice|sorted|'
             r'staticmethod|str|sum|super|tuple|type|unichr|unicode|'
             r'vars|xrange|zip)\b', Token.Name.Builtin),
             
            # Operators
            (r'!=|==|<<|>>|[-~+/*%=<>&^|.]', Token.Operator),
            
            # Numbers
            (r'(\d+\.\d*|\d*\.\d+)([eE][+-]?[0-9]+)?j?', Token.Number.Float),
            (r'\d+[eE][+-]?[0-9]+j?', Token.Number.Float),
            (r'0[0-7]+j?', Token.Number.Oct),
            (r'0[xX][a-fA-F0-9]+', Token.Number.Hex),
            (r'\d+L', Token.Number.Integer.Long),
            (r'\d+j?', Token.Number.Integer),
            
            # Strings
            (r'"(\\\\|\\"|[^"])*"', Token.String.Double),
            (r"'(\\\\|\\'|[^'])*'", Token.String.Single),
            (r'""".*?"""', Token.String.Double),
            (r"'''.*?'''", Token.String.Single),
            
            # Identifiers
            (r'[a-zA-Z_]\w*', Token.Name),
            
            # Punctuation
            (r'[(){}\[\],:;]', Token.Punctuation),
        ],
    }