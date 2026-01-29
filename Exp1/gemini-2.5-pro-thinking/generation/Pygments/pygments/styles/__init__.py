"""
    pygments.styles
    ~~~~~~~~~~~~~~~

    Contains the built-in styles.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from pygments.util import ClassNotFound
from pygments.token import Token

_STYLES = {}

def _import_styles():
    from . import default
    _STYLES['default'] = default.DefaultStyle

def get_style_by_name(name):
    if not _STYLES:
        _import_styles()
    if name in _STYLES:
        return _STYLES[name]
    raise ClassNotFound(f"Style '{name}' not found.")


class Style:
    """
    Base class for styles.
    """
    background_color = "#ffffff"
    highlight_color = "#ffffcc"

    styles = {}

    def __init__(self, **kwargs):
        self._styles = {}
        self._style_cache = {}
        self.styles.update(self.list_styles())
        self.styles.update(kwargs.get('style_overrides', {}))
        self.background_color = kwargs.get('background_color', self.background_color)
        self.highlight_color = kwargs.get('highlight_color', self.highlight_color)
        self.default_style = self.styles.get(Token, {})

    def _get_style_for_token(self, ttype):
        if ttype in self._style_cache:
            return self._style_cache[ttype]
        
        style = self.styles.get(ttype, {})
        parent = ttype.parent
        while parent is not None:
            parent_style = self.styles.get(parent, {})
            for key, value in parent_style.items():
                if key not in style:
                    style[key] = value
            parent = parent.parent
        
        self._style_cache[ttype] = style
        return style

    def __iter__(self):
        for ttype in self.styles:
            yield ttype, self._get_style_for_token(ttype)

    def list_styles(self):
        # This is a bit of a hack to get all token types
        # A real implementation would be more robust
        from pygments import token
        tokentypes = []
        def find_tokentypes(t):
            tokentypes.append(t)
            for name in dir(t):
                if name[0].isupper():
                    child = getattr(t, name)
                    if isinstance(child, tuple):
                        find_tokentypes(child)
        find_tokentypes(token.Token)
        
        base_styles = {}
        for ttype, definition in self.styles.items():
            if isinstance(definition, str):
                props = {
                    'color': None, 'bold': False, 'italic': False, 'underline': False,
                    'bgcolor': None, 'border': None
                }
                parts = definition.split()
                for part in parts:
                    if part == 'bold':
                        props['bold'] = True
                    elif part == 'italic':
                        props['italic'] = True
                    elif part == 'underline':
                        props['underline'] = True
                    elif part.startswith('#'):
                        props['color'] = part[1:]
                    elif part.startswith('bg:'):
                        props['bgcolor'] = part[3:]
                    elif part.startswith('border:'):
                        props['border'] = part[7:]
                base_styles[ttype] = props
            else:
                base_styles[ttype] = definition
        return base_styles

# From pygments.style
ansicolors = {
    # dark
    'black': '30', 'red': '31', 'green': '32', 'yellow': '33',
    'blue': '34', 'magenta': '35', 'cyan': '36', 'gray': '37',
    # bright
    'brightblack': '90', 'brightred': '91', 'brightgreen': '92',
    'brightyellow': '93', 'brightblue': '94', 'brightmagenta': '95',
    'brightcyan': '96', 'white': '97',
    # Aliases for compatibility
    '#000000': '30', '#aa0000': '31', '#00aa00': '32', '#aa5500': '33',
    '#0000aa': '34', '#aa00aa': '35', '#00aaaa': '36', '#aaaaaa': '37',
    '#555555': '90', '#ff5555': '91', '#55ff55': '92', '#ffff55': '93',
    '#5555ff': '94', '#ff55ff': '95', '#55ffff': '96', '#ffffff': '97',
}