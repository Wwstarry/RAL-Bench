"""
    pygments.formatters.terminal
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Formatter for terminal output with ANSI sequences.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from pygments.formatter import Formatter
from pygments.style import ansicolors

class TerminalFormatter(Formatter):
    """
    Format tokens with ANSI color sequences, for output in a text console.
    """
    name = 'Terminal'
    aliases = ['terminal', 'console']
    filenames = []

    def __init__(self, **options):
        Formatter.__init__(self, **options)
        self.colors = self._create_color_map()

    def _create_color_map(self):
        color_map = {}
        for ttype, style in self.style:
            ansicolor = ''
            if style['color']:
                try:
                    ansicolor = ansicolors[style['color']]
                except KeyError:
                    pass # color not in map
            if style['bold']:
                ansicolor += ';1'
            if style['underline']:
                ansicolor += ';4'
            if ansicolor:
                color_map[ttype] = ansicolor
        return color_map

    def format(self, tokensource, outfile):
        for ttype, value in tokensource:
            color = None
            while ttype not in self.colors:
                ttype = ttype.parent
                if ttype is None:
                    break
            
            color = self.colors.get(ttype)
            
            if color:
                # \x1b is the ESC character
                outfile.write(f'\x1b[{color}m{value}\x1b[0m')
            else:
                outfile.write(value)