"""
HTML formatter.
"""

from pygments.token import Token

class HtmlFormatter:
    """Format tokens as HTML."""
    
    def __init__(self, **options):
        self.options = options
        self.styles = self._get_styles()
        
    def _get_styles(self):
        """Get CSS styles for tokens."""
        return {
            Token: '',
            Token.Text: '',
            Token.Whitespace: '',
            Token.Escape: '',
            Token.Error: 'color: #FF0000',
            Token.Other: '',
            Token.Keyword: 'color: #008000; font-weight: bold',
            Token.Keyword.Constant: 'color: #008000; font-weight: bold',
            Token.Name: 'color: #000000',
            Token.Name.Builtin: 'color: #008000',
            Token.Name.Function: 'color: #0000FF',
            Token.Name.Class: 'color: #0000FF; font-weight: bold',
            Token.Literal.String: 'color: #BA2121',
            Token.Literal.String.Double: 'color: #BA2121',
            Token.Literal.String.Single: 'color: #BA2121',
            Token.Literal.Number: 'color: #080',
            Token.Operator: 'color: #666',
            Token.Punctuation: 'color: #666',
            Token.Comment: 'color: #408080; font-style: italic',
            Token.Comment.Single: 'color: #408080; font-style: italic',
        }
    
    def _get_css_class(self, token):
        """Get CSS class for a token."""
        # Convert token to CSS class name
        parts = []
        for part in token:
            if part:
                parts.append(part)
        return ' '.join(parts)
    
    def _get_style(self, token):
        """Get style for a token."""
        # Try exact match first
        if token in self.styles:
            return self.styles[token]
        
        # Try parent tokens
        for i in range(len(token) - 1, 0, -1):
            parent = token[:i]
            if parent in self.styles:
                return self.styles[parent]
        
        return self.styles.get(Token, '')
    
    def format(self, tokensource, lexer):
        """Format tokens as HTML."""
        out = []
        out.append('<div class="highlight">')
        out.append('<pre>')
        
        for ttype, value in tokensource:
            style = self._get_style(ttype)
            if style:
                out.append(f'<span style="{style}">{self._escape(value)}</span>')
            else:
                out.append(self._escape(value))
        
        out.append('</pre>')
        out.append('</div>')
        return ''.join(out)
    
    def get_style_defs(self, arg=None):
        """Get style definitions for CSS classes."""
        lines = []
        lines.append('.highlight { background: #f8f8f8; }')
        lines.append('.highlight pre { margin: 0; }')
        
        for token, style in self.styles.items():
            if style:
                classname = self._get_css_class(token)
                if classname:
                    lines.append(f'.highlight .{classname} {{ {style} }}')
        
        return '\n'.join(lines)
    
    def _escape(self, text):
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))