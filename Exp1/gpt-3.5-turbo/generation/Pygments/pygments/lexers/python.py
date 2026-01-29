import re
from pygments.lex import RegexLexer
from pygments.token import *

class PythonLexer(RegexLexer):
    name = 'Python'
    aliases = ['python', 'py']
    filenames = ['*.py', '*.pyw']

    _keywords = (
        'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del',
        'elif', 'else', 'except', 'exec', 'finally', 'for', 'from', 'global',
        'if', 'import', 'in', 'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'with', 'yield', 'async', 'await',
        'nonlocal',
    )

    _builtins = (
        'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes', 'callable',
        'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir',
        'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float', 'format',
        'frozenset', 'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex',
        'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len',
        'list', 'locals', 'map', 'max', 'memoryview', 'min', 'next', 'object',
        'oct', 'open', 'ord', 'pow', 'print', 'property', 'range', 'repr',
        'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod',
        'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip',
    )

    tokens = {
        'root': [
            (r'\n', Text),
            (r'[ \t]+', Whitespace),
            (r'#.*$', Comment.Single),
            (r'"""(\\\\|\\[^\\]|[^"\\])*"""', String.Doc),
            (r"'''(\\\\|\\[^\\]|[^'\\])*'''", String.Doc),
            (r'"(\\\\|\\[^\\]|[^"\\])*"', String.String),
            (r"'(\\\\|\\[^\\]|[^'\\])*'", String.String),
            (r'\b(' + '|'.join(re.escape(w) for w in _keywords) + r')\b', Keyword),
            (r'\b(' + '|'.join(re.escape(w) for w in _builtins) + r')\b', Name.Builtin),
            (r'[a-zA-Z_]\w*', Name),
            (r'\d+\.\d*([eE][+-]?\d+)?j?', Number.Float),
            (r'\d+[eE][+-]?\d+j?', Number.Float),
            (r'0x[0-9a-fA-F]+', Number.Hex),
            (r'\d+j?', Number.Integer),
            (r'==|!=|<=|>=|<>|<<|>>|[-+/*%=<>&^|~@]', Operator),
            (r'[{}()\[\],.;:]', Punctuation),
            (r'.', Error),
        ],
    }