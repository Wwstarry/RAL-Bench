import re
from pygments.token import Token

class IniLexer:
    """
    Minimal INI lexer.
    """
    name = 'INI'
    aliases = ['ini']
    filenames = ['*.ini']

    _section_re = re.compile(r'^\s*\[.*?\]\s*$', re.MULTILINE)
    _comment_re = re.compile(r'^\s*[;#].*$', re.MULTILINE)
    _keyval_re = re.compile(r'^\s*([^=:#\s]+)\s*([=:])\s*(.*?)\s*$', re.MULTILINE)
    _blank_re = re.compile(r'^\s*$', re.MULTILINE)

    def get_tokens(self, code):
        lines = code.splitlines(keepends=True)
        for line in lines:
            if self._blank_re.match(line):
                yield (Token.Text, line)
            elif self._comment_re.match(line):
                yield (Token.Comment, line)
            elif self._section_re.match(line):
                yield (Token.Name_Label, line)
            else:
                m = self._keyval_re.match(line)
                if m:
                    key, sep, val = m.groups()
                    start = line.find(key)
                    yield (Token.Name_Attribute, key)
                    yield (Token.Operator, sep)
                    if val:
                        yield (Token.Literal_String, val)
                    # Emit trailing whitespace/newline
                    rest = line[start+len(key)+len(sep)+len(val):]
                    if rest:
                        yield (Token.Text, rest)
                else:
                    # Unrecognized line
                    yield (Token.Error, line)