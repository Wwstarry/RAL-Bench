from pygments.token import Token, Text, Keyword, Name, String, Number, Operator, Punctuation, Comment, Generic

class TerminalFormatter:
    """
    Format tokens as ANSI colored output for terminals.
    """

    _colors = {
        # token type: (fg, bold)
        'Keyword': (34, True),       # blue bold
        'Name': (37, False),         # white
        'Name.Builtin': (36, False), # cyan
        'String': (32, False),       # green
        'Number': (35, False),       # magenta
        'Operator': (33, False),     # yellow
        'Punctuation': (33, False),  # yellow
        'Comment': (90, False),      # bright black (gray)
        'Generic': (37, False),      # white
        'Error': (31, True),         # red bold
        'Text': (0, False),          # default
        'Whitespace': (0, False),    # default
    }

    def __init__(self, **options):
        self.options = options
        self.noclasses = options.get('noclasses', False)
        self.ansi = options.get('ansi', True)

    def _get_ansi_code(self, ttype):
        # Find the closest matching token type in _colors
        while ttype and ttype != ():
            name = '.'.join(ttype)
            if name in self._colors:
                fg, bold = self._colors[name]
                code = ''
                if bold:
                    code += '\033[1m'
                if fg != 0:
                    code += f'\033[{fg}m'
                return code
            ttype = ttype[:-1]
        return ''

    def format(self, tokens):
        """
        Format a token stream and return ANSI colored string.
        """
        result = []
        for ttype, value in tokens:
            if self.noclasses or not self.ansi:
                result.append(value)
            else:
                code = self._get_ansi_code(ttype)
                reset = '\033[0m' if code else ''
                result.append(f'{code}{value}{reset}')
        return ''.join(result)