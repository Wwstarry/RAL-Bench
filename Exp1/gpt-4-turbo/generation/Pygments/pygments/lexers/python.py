import re
from pygments.token import Token
from pygments.util import ClassNotFound

class PythonLexer:
    """
    Minimal Python lexer.
    """
    name = 'Python'
    aliases = ['python', 'py']
    filenames = ['*.py']

    _keywords = set([
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
        'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
        'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
        'try', 'while', 'with', 'yield'
    ])
    _builtins = set([
        'abs', 'dict', 'help', 'min', 'setattr', 'all', 'dir', 'hex', 'next',
        'slice', 'any', 'divmod', 'id', 'object', 'sorted', 'ascii', 'enumerate',
        'input', 'oct', 'staticmethod', 'bin', 'eval', 'int', 'open', 'str',
        'bool', 'exec', 'isinstance', 'ord', 'sum', 'bytearray', 'filter',
        'issubclass', 'pow', 'super', 'bytes', 'float', 'iter', 'print', 'tuple',
        'callable', 'format', 'len', 'property', 'type', 'chr', 'frozenset',
        'list', 'range', 'vars', 'classmethod', 'getattr', 'locals', 'repr',
        'zip', 'compile', 'globals', 'map', 'reversed', '__import__', 'complex',
        'hasattr', 'max', 'round', 'delattr', 'hash', 'memoryview', 'set'
    ])

    _token_specification = [
        ('WHITESPACE', r'[ \t\n]+'),
        ('COMMENT',    r'\#.*'),
        ('STRING',     r'(?:[uU]?[rR]?|[rR]?[uU]?)("""(?:.|\n)*?"""|\'\'\'(?:.|\n)*?\'\'\'|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\')'),
        ('NUMBER',     r'\b\d+(\.\d*)?([eE][+-]?\d+)?j?\b'),
        ('NAME',       r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
        ('OP',         r'[\+\-\*/%&|\^~<>!]=?|==|!=|<=|>=|//|<<|>>|\*\*|\.\.\.|:='),
        ('PUNCT',      r'[\(\)\[\]\{\}\:\,\.\;]'),
        ('NEWLINE',    r'\n'),
        ('MISMATCH',   r'.'),
    ]
    _tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in _token_specification)
    _tok_re = re.compile(_tok_regex, re.MULTILINE)

    def get_tokens(self, code):
        for mo in self._tok_re.finditer(code):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'WHITESPACE':
                yield (Token.Text, value)
            elif kind == 'COMMENT':
                yield (Token.Comment, value)
            elif kind == 'STRING':
                yield (Token.Literal_String, value)
            elif kind == 'NUMBER':
                if value.endswith('j'):
                    yield (Token.Literal_Number, value)
                elif '.' in value or 'e' in value or 'E' in value:
                    yield (Token.Literal_Number_Float, value)
                else:
                    yield (Token.Literal_Number_Integer, value)
            elif kind == 'NAME':
                if value in self._keywords:
                    yield (Token.Keyword, value)
                elif value in self._builtins:
                    yield (Token.Name_Builtin, value)
                else:
                    yield (Token.Name, value)
            elif kind == 'OP':
                yield (Token.Operator, value)
            elif kind == 'PUNCT':
                yield (Token.Punctuation, value)
            elif kind == 'NEWLINE':
                yield (Token.Text, value)
            elif kind == 'MISMATCH':
                yield (Token.Error, value)