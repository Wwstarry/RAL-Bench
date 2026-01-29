"""
Terminal formatter for Pygments.
"""

from pygments.token import Token
from pygments.util import get_bool_opt


class TerminalFormatter:
    """Formatter for terminal output with optional ANSI colors."""
    
    name = 'Terminal'
    aliases = ['terminal', 'console']
    filenames = []
    
    ANSI_COLORS = {
        'black': 30,
        'red': 31,
        'green': 32,
        'yellow': 33,
        'blue': 34,
        'magenta': 35,
        'cyan': 36,
        'white': 37,
        'gray': 90,
        'brightred': 91,
        'brightgreen': 92,
        'brightyellow': 93,
        'brightblue': 94,
        'brightmagenta': 95,
        'brightcyan': 96,
        'brightwhite': 97,
    }
    
    TOKEN_COLORS = {
        Token.Comment: 'gray',
        Token.Comment.Single: 'gray',
        Token.Comment.Multiline: 'gray',
        Token.Keyword: 'blue',
        Token.Keyword.Constant: 'blue',
        Token.Keyword.Declaration: 'blue',
        Token.Keyword.Namespace: 'blue',
        Token.Keyword.Pseudo: 'blue',
        Token.Keyword.Reserved: 'blue',
        Token.Keyword.Type: 'blue',
        Token.Name.Builtin: 'cyan',
        Token.Name.Class: 'green',
        Token.Name.Function: 'green',
        Token.String: 'red',
        Token.String.Double: 'red',
        Token.String.Single: 'red',
        Token.Number: 'magenta',
        Token.Number.Integer: 'magenta',
        Token.Number.Float: 'magenta',
        Token.Operator: 'white',
        Token.Error: 'brightred',
    }
    
    def __init__(self, **options):
        self.encoding = options.get('encoding', 'utf-8')
        self.nowrap = get_bool_opt(options, 'nowrap', False)
        self.bg = options.get('bg', 'dark')
        self.colorize = get_bool_opt(options, 'colorize', True)
    
    def _get_color_code(self, token):
        """Get ANSI color code for a token."""
        if not self.colorize:
            return ''
        
        current = token
        while current:
            if current in self.TOKEN_COLORS:
                color_name = self.TOKEN_COLORS[current]
                if color_name in self.ANSI_COLORS:
                    code = self.ANSI_COLORS[color_name]
                    return f'\033[{code}m'
            
            if hasattr(current, 'parent'):
                current = current.parent
            else:
                break
        
        return ''
    
    def format(self, tokens):
        """Format tokens for terminal output."""
        result = []
        
        for token, value in tokens:
            if not value:
                continue
            
            color_code = self._get_color_code(token)
            reset_code = '\033[0m' if color_code else ''
            
            if color_code:
                result.append(color_code)
                result.append(value)
                result.append(reset_code)
            else:
                result.append(value)
        
        return ''.join(result)