import re
from typing import Optional, List, Dict, Any

class Text:
    def __init__(self, text: str = "", style: Optional[str] = None, emoji: bool = True, justify: Optional[str] = None, end: str = "\n"):
        self.text = text
        self.style = style
        self.emoji = emoji
        self.justify = justify
        self.end = end

    def append(self, text: str, style: Optional[str] = None):
        self.text += text

    def __rich__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        out = self.text
        # Emoji handling
        if self.emoji:
            from .console import _replace_emoji
            out = _replace_emoji(out)
        # Style handling
        if self.style:
            from .console import _apply_style
            out = _apply_style(out, self.style)
        # Justify
        if self.justify:
            width = 80
            if self.justify == "center":
                out = out.center(width)
            elif self.justify == "right":
                out = out.rjust(width)
            else:
                out = out.ljust(width)
        return out + self.end