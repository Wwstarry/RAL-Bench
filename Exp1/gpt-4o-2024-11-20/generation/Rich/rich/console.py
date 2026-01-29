# rich/console.py

import sys
from .text import Text
from .theme import Theme

class Console:
    def __init__(self, theme=None):
        self.theme = theme or Theme()
        self.output = sys.stdout

    def print(self, *objects, sep=" ", end="\n", style=None):
        styled_text = sep.join(str(obj) for obj in objects)
        if style:
            styled_text = self.theme.apply_style(styled_text, style)
        self.output.write(styled_text + end)

    def render_text(self, text: Text):
        self.output.write(text.render() + "\n")