import sys
import re
from .text import Text
from .theme import Theme

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")

def _strip_ansi(text):
    return _ANSI_ESCAPE_RE.sub("", text)

def _ansi_len(text):
    return len(_strip_ansi(text))

def _apply_style(text, style):
    # style is a dict with keys like 'color', 'bold', 'italic', 'underline'
    # For simplicity, support color names and bold only
    codes = []
    if not style:
        return text
    color = style.get("color")
    if color:
        # map some basic colors to ANSI codes
        colors = {
            "black": "30",
            "red": "31",
            "green": "32",
            "yellow": "33",
            "blue": "34",
            "magenta": "35",
            "cyan": "36",
            "white": "37",
            "bright_black": "90",
            "bright_red": "91",
            "bright_green": "92",
            "bright_yellow": "93",
            "bright_blue": "94",
            "bright_magenta": "95",
            "bright_cyan": "96",
            "bright_white": "97",
        }
        code = colors.get(color.lower())
        if code:
            codes.append(code)
    if style.get("bold"):
        codes.append("1")
    if style.get("italic"):
        codes.append("3")
    if style.get("underline"):
        codes.append("4")
    if codes:
        return f"\x1b[{';'.join(codes)}m{text}\x1b[0m"
    return text

def _emoji_replace(text):
    # Simple emoji replacement for some common emojis
    emoji_map = {
        ":smile:": "😄",
        ":heart:": "❤️",
        ":thumbs_up:": "👍",
        ":star:": "⭐",
        ":fire:": "🔥",
        ":check:": "✔️",
        ":cross:": "❌",
        ":warning:": "⚠️",
        ":rocket:": "🚀",
        ":sparkles:": "✨",
    }
    for k, v in emoji_map.items():
        text = text.replace(k, v)
    return text

class Console:
    def __init__(self, file=None, theme=None, emoji=True, markup=True, width=80):
        self.file = file or sys.stdout
        self.theme = theme or Theme()
        self.emoji = emoji
        self.markup = markup
        self.width = width

    def print(self, *objects, sep=" ", end="\n", style=None, markup=None, emoji=None):
        # Compose text from objects
        texts = []
        for obj in objects:
            if isinstance(obj, Text):
                texts.append(obj)
            else:
                texts.append(Text(str(obj)))
        text = Text.assemble(*texts)
        # Apply emoji
        if emoji if emoji is not None else self.emoji:
            text = text.emoji_replace()
        # Apply markup
        if markup if markup is not None else self.markup:
            text = text.markup(self.theme)
        # Apply style
        if style:
            text.stylize(style)
        # Wrap text
        lines = text.wrap(self.width)
        for i, line in enumerate(lines):
            self.file.write(line.plain + (end if i == len(lines) - 1 else "\n"))
        self.file.flush()

    def rule(self, title="", style=None, align="center", char="─"):
        # Print a rule line with optional title
        width = self.width
        title_text = Text(title)
        if self.emoji:
            title_text = title_text.emoji_replace()
        if self.markup:
            title_text = title_text.markup(self.theme)
        title_str = title_text.plain
        title_len = len(title_str)
        if title_len + 2 >= width:
            line = char * width
        else:
            left_len = (width - title_len - 2) // 2
            right_len = width - title_len - 2 - left_len
            if align == "left":
                left_len = 0
                right_len = width - title_len - 2
            elif align == "right":
                left_len = width - title_len - 2
                right_len = 0
            line = char * left_len + " " + title_str + " " + char * right_len
        self.file.write(line + "\n")
        self.file.flush()