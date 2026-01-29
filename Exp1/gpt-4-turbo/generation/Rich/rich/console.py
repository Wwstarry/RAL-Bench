import sys
import re
from typing import Any, Optional, List, Dict, Union
from .text import Text
from .theme import Theme

# Basic ANSI color codes
ANSI_COLORS = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "bright_black": 90,
    "bright_red": 91,
    "bright_green": 92,
    "bright_yellow": 93,
    "bright_blue": 94,
    "bright_magenta": 95,
    "bright_cyan": 96,
    "bright_white": 97,
    "default": 39,
}

STYLE_RE = re.compile(r"\[(?P<style>[a-zA-Z0-9_]+)\]")

EMOJI_MAP = {
    ":smile:": "😄",
    ":rocket:": "🚀",
    ":thumbs_up:": "👍",
    ":fire:": "🔥",
    ":star:": "⭐",
    ":check_mark:": "✅",
    ":x:": "❌",
    ":warning:": "⚠️",
    ":heart:": "❤️",
    ":sparkles:": "✨",
    # Add more as needed
}

def _replace_emoji(text: str) -> str:
    for code, emoji in EMOJI_MAP.items():
        text = text.replace(code, emoji)
    return text

def _apply_style(text: str, style: str) -> str:
    code = ANSI_COLORS.get(style, None)
    if code is not None:
        return f"\033[{code}m{text}\033[0m"
    return text

def _parse_markup(text: str, theme: Optional[Theme] = None) -> str:
    # Parse [style]text[/style] markup
    def replacer(match):
        style = match.group("style")
        return f"\033[{ANSI_COLORS.get(style, 39)}m"
    # Replace [style]
    out = ""
    pos = 0
    for m in STYLE_RE.finditer(text):
        out += text[pos:m.start()]
        style = m.group("style")
        ansi = f"\033[{ANSI_COLORS.get(style, 39)}m"
        out += ansi
        pos = m.end()
    out += text[pos:]
    # Reset at end
    if "\033[" in out:
        out += "\033[0m"
    return out

class Console:
    def __init__(self, file=None, theme: Optional[Theme] = None, width: Optional[int] = None):
        self.file = file or sys.stdout
        self.theme = theme or Theme()
        self.width = width or 80

    def print(self, *objects: Any, sep: str = " ", end: str = "\n", style: Optional[str] = None, emoji: bool = True, highlight: bool = False, markup: bool = True, wrap: bool = False) -> None:
        output = sep.join(str(obj) for obj in objects)
        if emoji:
            output = _replace_emoji(output)
        if markup:
            output = _parse_markup(output, self.theme)
        if style:
            output = _apply_style(output, style)
        if wrap and self.width:
            output = self._wrap_text(output, self.width)
        self.file.write(output + end)
        self.file.flush()

    def _wrap_text(self, text: str, width: int) -> str:
        lines = []
        for line in text.splitlines():
            while len(line) > width:
                lines.append(line[:width])
                line = line[width:]
            lines.append(line)
        return "\n".join(lines)

    def rule(self, title: str = "", style: Optional[str] = None) -> None:
        line = "-" * self.width
        if title:
            title = f" {title} "
            mid = self.width // 2 - len(title) // 2
            line = line[:mid] + title + line[mid + len(title):]
        if style:
            line = _apply_style(line, style)
        self.print(line)

    def input(self, prompt: str = "") -> str:
        self.print(prompt, end="")
        return input()

    def show(self, obj: Any) -> None:
        # For objects with __rich__, call it
        if hasattr(obj, "__rich__"):
            self.print(obj.__rich__())
        else:
            self.print(str(obj))