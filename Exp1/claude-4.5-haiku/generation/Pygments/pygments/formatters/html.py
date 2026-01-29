"""
HTML formatter for Pygments.
"""

from pygments.token import Token
from pygments.util import get_bool_opt, get_int_opt
from pygments.styles.default import DefaultStyle


class HtmlFormatter:
    """Formatter for HTML output."""
    
    name = 'HTML'
    aliases = ['html']
    filenames = ['*.html', '*.htm']
    
    def __init__(self, **options):
        self.full = get_bool_opt(options, 'full', False)
        self.style = options.get('style', DefaultStyle)
        self.noclasses = get_bool_opt(options, 'noclasses', False)
        self.doctype = options.get('doctype', 'html')
        self.encoding = options.get('encoding', 'utf-8')
        self.title = options.get('title', '')
        self.nowrap = get_bool_opt(options, 'nowrap', False)
        self.lineanchors = get_bool_opt(options, 'lineanchors', False)
        self.linenos = get_bool_opt(options, 'linenos', False)
        self.linespans = options.get('linespans', '')
        self.anchorlinenos = get_bool_opt(options, 'anchorlinenos', False)
        self.wrapcode = get_bool_opt(options, 'wrapcode', False)
        self.lineseparator = options.get('lineseparator', '\n')
        self.linenostart = get_int_opt(options, 'linenostart', 1)
        self.tagsfile = options.get('tagsfile', '')
        self.tagurlformat = options.get('tagurlformat', '')
        self.cssclass = options.get('cssclass', 'highlight')
        self.cssstyles = options.get('cssstyles', '')
        self.prestyles = options.get('prestyles', '')
        
        self._create_stylesheet()
    
    def _create_stylesheet(self):
        """Create the stylesheet for token types."""
        self.styles = {}
        if hasattr(self.style, 'styles'):
            self.styles = self.style.styles.copy()
    
    def _get_style(self, token):
        """Get the style for a token."""
        while token:
            if token in self.styles:
                return self.styles[token]
            if hasattr(token, 'parent'):
                token = token.parent
            else:
                break
        return {}
    
    def _escape_html(self, text):
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def format(self, tokens):
        """Format tokens as HTML."""
        if self.nowrap:
            return self._format_tokens(tokens)
        
        html = []
        
        if self.full:
            html.append('<!DOCTYPE html>\n')
            html.append('<html>\n')
            html.append('<head>\n')
            if self.title:
                html.append(f'<title>{self._escape_html(self.title)}</title>\n')
            html.append('<meta charset="utf-8">\n')
            html.append('<style>\n')
            html.append(self.get_style_defs())
            html.append('</style>\n')
            html.append('</head>\n')
            html.append('<body>\n')
        
        html.append(f'<pre class="{self.cssclass}">')
        html.append(self._format_tokens(tokens))
        html.append('</pre>\n')
        
        if self.full:
            html.append('</body>\n')
            html.append('</html>\n')
        
        return ''.join(html)
    
    def _format_tokens(self, tokens):
        """Format tokens as HTML spans."""
        html = []
        for token, value in tokens:
            if not value:
                continue
            
            style = self._get_style(token)
            escaped = self._escape_html(value)
            
            if self.noclasses or not style:
                html.append(escaped)
            else:
                color = style.get('color', '')
                bold = style.get('bold', False)
                italic = style.get('italic', False)
                underline = style.get('underline', False)
                bgcolor = style.get('bgcolor', '')
                
                css_parts = []
                if color:
                    css_parts.append(f'color: #{color}')
                if bold:
                    css_parts.append('font-weight: bold')
                if italic:
                    css_parts.append('font-style: italic')
                if underline:
                    css_parts.append('text-decoration: underline')
                if bgcolor:
                    css_parts.append(f'background-color: #{bgcolor}')
                
                if css_parts:
                    style_str = '; '.join(css_parts)
                    html.append(f'<span style="{style_str}">{escaped}</span>')
                else:
                    html.append(escaped)
        
        return ''.join(html)
    
    def get_style_defs(self, arg=''):
        """Get CSS style definitions."""
        css = []
        css.append(f'.{self.cssclass} {{ background-color: #f8f8f8; }}\n')
        
        for token, style in self.styles.items():
            if not style:
                continue
            
            token_str = str(token).replace('Token.', '').replace('.', '-').lower()
            css_parts = []
            
            if 'color' in style:
                css_parts.append(f'color: #{style["color"]}')
            if style.get('bold'):
                css_parts.append('font-weight: bold')
            if style.get('italic'):
                css_parts.append('font-style: italic')
            if style.get('underline'):
                css_parts.append('text-decoration: underline')
            if 'bgcolor' in style:
                css_parts.append(f'background-color: #{style["bgcolor"]}')
            
            if css_parts:
                css.append(f'.{self.cssclass} .{token_str} {{ {"; ".join(css_parts)}; }}\n')
        
        return ''.join(css)