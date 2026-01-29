"""
    pygments.formatters.html
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Formatter for HTML output.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from pygments.formatter import Formatter
from pygments.token import Token, is_token_subtype
from pygments.util import get_bool_opt, get_int_opt

_escape_html_table = {
    ord('&'): '&amp;',
    ord('<'): '&lt;',
    ord('>'): '&gt;',
    ord('"'): '&quot;',
    ord("'"): '&#39;',
}

def escape_html(text):
    return text.translate(_escape_html_table)


class HtmlFormatter(Formatter):
    """
    Format tokens as HTML 4 ``<span>`` tags.
    """
    name = 'HTML'
    aliases = ['html']
    filenames = ['*.html', '*.htm']

    def __init__(self, **options):
        Formatter.__init__(self, **options)
        self.full = get_bool_opt(options, 'full', False)
        self.title = options.get('title', '')
        self.noclasses = get_bool_opt(options, 'noclasses', False)
        self.classprefix = options.get('classprefix', '')
        self.cssclass = options.get('cssclass', 'highlight')
        self.linenos = get_bool_opt(options, 'linenos', False)
        self.lineseparator = options.get('lineseparator', '\n')

        self._create_stylesheet()

    def _create_stylesheet(self):
        self.stylesheet = {}
        self.class_map = {}
        for ttype, style in self.style:
            cls = self._get_css_class(ttype)
            if cls:
                self.class_map[ttype] = cls
            
            style_rules = []
            if style['color']:
                style_rules.append(f"color: #{style['color']}")
            if style['bold']:
                style_rules.append("font-weight: bold")
            if style['italic']:
                style_rules.append("font-style: italic")
            if style['underline']:
                style_rules.append("text-decoration: underline")
            if style['bgcolor']:
                style_rules.append(f"background-color: #{style['bgcolor']}")
            if style['border']:
                style_rules.append(f"border: 1px solid #{style['border']}")
            
            if style_rules:
                self.stylesheet[ttype] = '; '.join(style_rules)

    def _get_css_class(self, ttype):
        if ttype in self.class_map:
            return self.class_map[ttype]
        
        c = ttype
        while c not in self.style:
            c = c.parent
            if c is None:
                return ''
        
        path = []
        while c.parent is not None:
            path.insert(0, str(c).split('.')[-1])
            c = c.parent
        
        # Abbreviate token names
        # e.g. Token.Keyword.Constant -> kc
        abbrevs = {
            'Comment': 'c', 'Keyword': 'k', 'Name': 'n', 'Literal': 'l',
            'String': 's', 'Number': 'm', 'Operator': 'o', 'Punctuation': 'p',
            'Generic': 'g', 'Text': 'x', 'Error': 'err', 'Whitespace': 'w',
            'Constant': 'kc', 'Declaration': 'kd', 'Namespace': 'kn',
            'Pseudo': 'kp', 'Reserved': 'kr', 'Type': 'kt', 'Variable': 'nv',
            'Function': 'nf', 'Class': 'nc', 'Attribute': 'na', 'Tag': 'nt',
            'Builtin': 'nb', 'Decorator': 'nd', 'Single': 's1', 'Double': 's2',
            'Doc': 'sd', 'Interpol': 'si', 'Regex': 'sr', 'Integer': 'mi',
            'Float': 'mf', 'Hex': 'mh', 'Oct': 'mo', 'Word': 'ow',
            'Heading': 'gh', 'Subheading': 'gu', 'Deleted': 'gd', 'Inserted': 'gi',
            'Output': 'go', 'Prompt': 'gp', 'Traceback': 'gt', 'Error': 'gr',
            'Emph': 'ge', 'Strong': 'gs',
        }
        
        parts = []
        for p in str(ttype).split('.')[1:]:
            parts.append(abbrevs.get(p, p.lower()))
        
        return self.classprefix + ''.join(parts)

    def get_style_defs(self, arg=''):
        if not arg:
            arg = '.' + self.cssclass
        
        lines = []
        # background
        bg_color = self.style.background_color
        lines.append(f"{arg} {{ background: {bg_color}; color: {self.style.default_style.get('color', '#000000')} }}")

        for ttype, style in self.style:
            cls = self._get_css_class(ttype)
            if cls:
                style_str = self.stylesheet.get(ttype, '')
                if style_str:
                    lines.append(f"{arg} .{cls} {{ {style_str} }}")
        return '\n'.join(lines)

    def format_unencoded(self, tokensource, outfile):
        if self.full:
            outfile.write('<!DOCTYPE html>\n')
            outfile.write('<html>\n<head>\n')
            outfile.write(f'  <title>{escape_html(self.title)}</title>\n')
            outfile.write('  <style type="text/css">\n')
            outfile.write(self.get_style_defs())
            outfile.write('\n  </style>\n</head>\n<body>\n')

        outfile.write(f'<div class="{self.cssclass}">')
        # In this simplified version, we don't implement line numbers or other complex features
        # We just wrap tokens in spans.
        
        if not self.noclasses:
            outfile.write('<pre>')
            for ttype, value in tokensource:
                cssclass = self._get_css_class(ttype)
                if cssclass:
                    outfile.write(f'<span class="{cssclass}">')
                outfile.write(escape_html(value))
                if cssclass:
                    outfile.write('</span>')
            outfile.write('</pre>')
        else: # inline styles
            outfile.write('<pre>')
            for ttype, value in tokensource:
                style = self.stylesheet.get(ttype)
                while not style and ttype.parent:
                    ttype = ttype.parent
                    style = self.stylesheet.get(ttype)
                
                if style:
                    outfile.write(f'<span style="{style}">')
                outfile.write(escape_html(value))
                if style:
                    outfile.write('</span>')
            outfile.write('</pre>')

        outfile.write('</div>\n')

        if self.full:
            outfile.write('</body>\n</html>\n')

    def format(self, tokensource, outfile):
        # The real pygments has a complex encoding handling system.
        # We'll assume UTF-8 is fine.
        self.format_unencoded(tokensource, outfile)