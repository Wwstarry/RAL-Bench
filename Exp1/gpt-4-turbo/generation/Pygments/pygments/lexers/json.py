import re
from pygments.token import Token

class JsonLexer:
    """
    Minimal JSON lexer.
    """
    name = 'JSON'
    aliases = ['json']
    filenames = ['*.json']

    _token_specification = [
        ('WHITESPACE', r'[ \t\n\r]+'),
        ('NUMBER',     r'-?\d+(\.\d+)?([eE][+-]?\d+)?'),
        ('STRING',     r'"(\\\\|\\"|[^"])*"'),
        ('TRUE',       r'\btrue\b'),
        ('FALSE',      r'\bfalse\b'),
        ('NULL',       r'\bnull\b'),
        ('PUNCT',      r'[{}\[\]:,]'),
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
            elif kind == 'NUMBER':
                if '.' in value or 'e' in value or 'E' in value:
                    yield (Token.Literal_Number_Float, value)
                else:
                    yield (Token.Literal_Number_Integer, value)
            elif kind == 'STRING':
                yield (Token.Literal_String_Double, value)
            elif kind == 'TRUE' or kind == 'FALSE':
                yield (Token.Keyword_Constant, value)
            elif kind == 'NULL':
                yield (Token.Keyword_Constant, value)
            elif kind == 'PUNCT':
                yield (Token.Punctuation, value)
            elif kind == 'MISMATCH':
                yield (Token.Error, value)