from pygments.token import Token, STANDARD_TYPES
from pygments.styles.default import DefaultStyle

class HtmlFormatter:
    """
    Minimal HTML formatter.
    """
    name = 'HTML'
    aliases = ['html']

    def __init__(self, style='default', noclasses=False, **options):
        self.noclasses = noclasses
        self.style = DefaultStyle
        self.styles = self._build_styles()

    def _build_styles(self):
        # Map token types to CSS
        styles = {}
        for ttype, styledef in self.style.styles.items():
            css = []
            if styledef:
                for part in styledef.split():
                    if part == 'bold':
                        css.append('font-weight: bold')
                    elif part == 'italic':
                        css.append('font-style: italic')
                    elif part.startswith('bg:'):
                        css.append('background-color: #%s' % part[3:])
                    elif part.startswith('#'):
                        css.append('color: %s' % part)
            styles[ttype] = '; '.join(css)
        return styles

    def _get_css_class(self, ttype):
        # Use class names like 'k', 'n', etc.
        # We'll use the last part of the token name
        name = ttype.name
        short = {
            'Keyword': 'k',
            'Name': 'n',
            'Comment': 'c',
            'Literal': 'l',
            'String': 's',
            'Number': 'm',
            'Operator': 'o',
            'Punctuation': 'p',
            'Generic': 'g',
            'Error': 'err',
            'Text': 't',
            'Whitespace': 'w',
        }
        for key, val in short.items():
            if name.startswith(key):
                return val
        return 'x'

    def get_style_defs(self, arg=''):
        # Return CSS definitions for the style
        lines = []
        for ttype, style in self.styles.items():
            if style:
                class_name = self._get_css_class(ttype)
                lines.append('.%s { %s }' % (class_name, style))
        return '\n'.join(lines)

    def format(self, tokensource, outfile=None):
        # Return HTML string
        html = []
        for ttype, value in tokensource:
            style = self.styles.get(ttype, '')
            if self.noclasses:
                if style:
                    html.append('<span style="%s">%s</span>' % (style, self._html_escape(value)))
                else:
                    html.append(self._html_escape(value))
            else:
                class_name = self._get_css_class(ttype)
                html.append('<span class="%s">%s</span>' % (class_name, self._html_escape(value)))
        result = ''.join(html)
        if outfile is not None:
            outfile.write(result)
            return None
        return result

    def _html_escape(self, value):
        return (value.replace('&', '&amp;')
                     .replace('<', '&lt;')
                     .replace('>', '&gt;')
                     .replace('"', '&quot;'))