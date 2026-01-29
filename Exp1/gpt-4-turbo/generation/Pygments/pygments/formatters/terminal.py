from pygments.token import Token, STANDARD_TYPES
from pygments.styles.default import DefaultStyle

_ansi_colors = {
    'black': '30', 'red': '31', 'green': '32', 'yellow': '33',
    'blue': '34', 'magenta': '35', 'cyan': '36', 'white': '37',
    'brightblack': '90', 'brightred': '91', 'brightgreen': '92',
    'brightyellow': '93', 'brightblue': '94', 'brightmagenta': '95',
    'brightcyan': '96', 'brightwhite': '97'
}

def _color_for_token(ttype, style):
    # Only basic color support
    if not style:
        return ''
    fg = None
    bold = False
    for part in style.split():
        if part == 'bold':
            bold = True
        elif part.startswith('#'):
            # Map some common colors
            if part == '#008000':
                fg = 'green'
            elif part == '#0000FF':
                fg = 'blue'
            elif part == '#FF0000':
                fg = 'red'
            elif part == '#808080':
                fg = 'brightblack'
            elif part == '#800000':
                fg = 'red'
            elif part == '#000080':
                fg = 'blue'
            elif part == '#800080':
                fg = 'magenta'
            elif part == '#008080':
                fg = 'cyan'
            elif part == '#808000':
                fg = 'yellow'
            elif part == '#C0C0C0':
                fg = 'white'
    seq = []
    if fg and fg in _ansi_colors:
        seq.append(_ansi_colors[fg])
    if bold:
        seq.append('1')
    if seq:
        return '\x1b[%sm' % ';'.join(seq)
    return ''

class TerminalFormatter:
    """
    Minimal terminal formatter with ANSI colors.
    """
    name = 'Terminal'
    aliases = ['terminal', 'ansi']

    def __init__(self, style='default', **options):
        self.style = DefaultStyle
        self.styles = self._build_styles()

    def _build_styles(self):
        styles = {}
        for ttype, styledef in self.style.styles.items():
            styles[ttype] = styledef
        return styles

    def format(self, tokensource, outfile=None):
        out = []
        for ttype, value in tokensource:
            style = self.styles.get(ttype, '')
            color = _color_for_token(ttype, style)
            if color:
                out.append('%s%s\x1b[0m' % (color, value))
            else:
                out.append(value)
        result = ''.join(out)
        if outfile is not None:
            outfile.write(result)
            return None
        return result