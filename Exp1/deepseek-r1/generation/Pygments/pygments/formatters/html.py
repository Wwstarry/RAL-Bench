"""
HTML formatter.
"""

from pygments.formatter import Formatter
from pygments.token import Token
from pygments.util import get_bool_opt, get_int_opt, get_list_opt

__all__ = ['HtmlFormatter']

class HtmlFormatter(Formatter):
    """Formatter for HTML output."""
    
    def __init__(self, **options):
        super().__init__(**options)
        self.noclasses = get_bool_opt(options, 'noclasses', False)
        self.classprefix = options.get('classprefix', '')
        self.cssstyles = options.get('cssstyles', '')
        self.prestyles = options.get('prestyles', '')
        self.cssfile = options.get('cssfile', '')
        self.noclobber_cssfile = get_bool_opt(options, 'noclobber_cssfile', False)
        self.linenos = get_bool_opt(options, 'linenos', False)
        self.hl_lines = get_list_opt(options, 'hl_lines', [])
        
    def _get_css_class(self, token):
        """Get CSS class for token."""
        if self.noclasses:
            return ''
        cls = token.__class__.__name__.lower()
        if cls == '_tokentype':
            cls = 'text'
        return self.classprefix + cls
    
    def _get_css_style(self, token):
        """Get CSS style for token."""
        # Simple default styles
        styles = {
            'keyword': 'font-weight: bold',
            'keyword.constant': 'font-weight: bold; color: #007020',
            'name': 'color: #333',
            'literal.string': 'color: #4070a0',
            'literal.number': 'color: #40a070',
            'comment': 'color: #60a0b0; font-style: italic',
            'operator': 'color: #666',
            'punctuation': 'color: #666',
            'error': 'background-color: #f00; color: #fff',
        }
        
        cls = token.__class__.__name__.lower()
        if cls == '_tokentype':
            cls = 'text'
        return styles.get(cls, '')
        
    def format(self, tokensource):
        """Format token stream to HTML."""
        out = []
        out.append('<div class="highlight">')
        if self.cssstyles:
            out.append(f'<style>{self.cssstyles}</style>')
        
        out.append('<pre')
        if self.prestyles:
            out.append(f' style="{self.prestyles}"')
        out.append('>')
        
        for token, value in tokensource:
            if not value:
                continue
                
            if self.noclasses:
                style = self._get_css_style(token)
                if style:
                    out.append(f'<span style="{style}">{value}</span>')
                else:
                    out.append(value)
            else:
                cls = self._get_css_class(token)
                if cls:
                    out.append(f'<span class="{cls}">{value}</span>')
                else:
                    out.append(value)
        
        out.append('</pre></div>')
        return ''.join(out)
    
    def get_style_defs(self, arg=None):
        """Get CSS style definitions."""
        if self.noclasses:
            return ''
        
        # Simple default CSS
        css = """
.highlight .keyword { font-weight: bold; }
.highlight .keyword.constant { font-weight: bold; color: #007020; }
.highlight .name { color: #333; }
.highlight .literal.string { color: #4070a0; }
.highlight .literal.number { color: #40a070; }
.highlight .comment { color: #60a0b0; font-style: italic; }
.highlight .operator { color: #666; }
.highlight .punctuation { color: #666; }
.highlight .error { background-color: #f00; color: #fff; }
"""
        return css