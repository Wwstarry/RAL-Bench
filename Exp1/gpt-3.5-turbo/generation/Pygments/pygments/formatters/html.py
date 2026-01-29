from pygments.token import Token, Text, Keyword, Name, String, Number, Operator, Punctuation, Comment, Generic

class HtmlFormatter:
    """
    Format tokens as HTML with CSS classes.
    """

    def __init__(self, **options):
        self.options = options
        self.cssclass = options.get('cssclass', 'highlight')
        self.noclasses = options.get('noclasses', False)
        self.style = options.get('style', None)  # Not used for now

    def _get_css_class(self, ttype):
        # Map token type to CSS class name
        # e.g. Token.Keyword -> 'k', Token.Name.Function -> 'nf'
        # We'll use a simple mapping: first letters of token parts
        parts = ttype
        if not parts:
            return ''
        # Map common token types to short class names
        mapping = {
            'Text': 't',
            'Whitespace': 'w',
            'Error': 'err',
            'Other': 'o',
            'Keyword': 'k',
            'Name': 'n',
            'Literal': 'l',
            'String': 's',
            'Number': 'm',
            'Operator': 'o',
            'Punctuation': 'p',
            'Comment': 'c',
            'Generic': 'g',
        }
        cls = ''
        for part in parts:
            if part in mapping:
                cls += mapping[part]
            else:
                cls += part[0].lower()
        return cls

    def format(self, tokens):
        """
        Format a token stream and return HTML string.
        """
        html = []
        html.append(f'<div class="{self.cssclass}">')
        for ttype, value in tokens:
            if self.noclasses:
                # Escape HTML special chars
                escaped = (value.replace('&', '&amp;')
                                .replace('<', '&lt;')
                                .replace('>', '&gt;')
                                .replace('"', '&quot;'))
                html.append(escaped)
            else:
                cls = self._get_css_class(ttype)
                escaped = (value.replace('&', '&amp;')
                                .replace('<', '&lt;')
                                .replace('>', '&gt;')
                                .replace('"', '&quot;'))
                if cls:
                    html.append(f'<span class="{cls}">{escaped}</span>')
                else:
                    html.append(escaped)
        html.append('</div>')
        return ''.join(html)

    def get_style_defs(self, arg=''):
        """
        Return CSS style definitions for the formatter.
        """
        # Minimal style definitions for classes used above
        styles = {
            'k': 'color: #008000; font-weight: bold;',  # Keyword
            'n': 'color: #0000FF;',  # Name
            's': 'color: #BA2121;',  # String
            'm': 'color: #666666;',  # Number
            'o': 'color: #AA22FF;',  # Operator
            'p': 'color: #000000;',  # Punctuation
            'c': 'color: #408080; font-style: italic;',  # Comment
            'g': 'color: #999999;',  # Generic
            't': '',  # Text
            'w': '',  # Whitespace
            'err': 'border: 1px solid red;',  # Error
        }
        lines = []
        cssclass = self.cssclass or 'highlight'
        for cls, style in styles.items():
            lines.append(f'.{cssclass} .{cls} {{ {style} }}')
        return '\n'.join(lines)