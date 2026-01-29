import re
import sys
from collections import namedtuple

# --- Style and Color Handling ---

_COLORS = {
    "black": 30, "red": 31, "green": 32, "yellow": 33, "blue": 34, "magenta": 35, "cyan": 36, "white": 37,
    "bright_black": 90, "bright_red": 91, "bright_green": 92, "bright_yellow": 93, "bright_blue": 94, "bright_magenta": 95, "bright_cyan": 96, "bright_white": 97,
}
_STYLES = {"bold": 1, "dim": 2, "italic": 3, "underline": 4, "blink": 5, "reverse": 7, "strike": 9}
_RESET = "\x1b[0m"

def _style_to_ansi(style_str):
    if not style_str:
        return ""
    parts = style_str.split()
    codes = []
    for part in parts:
        if part in _STYLES:
            codes.append(str(_STYLES[part]))
        elif part in _COLORS:
            codes.append(str(_COLORS[part]))
    if not codes:
        return ""
    return f"\x1b[{';'.join(codes)}m"

def _strip_ansi(text):
    return re.sub(r"\x1b\[.*?m", "", text)

# --- Emoji Handling ---

_EMOJI = {
    ":v:": "\u270c\ufe0f",
    ":+1:": "\U0001f44d",
    ":smile:": "\U0001f604",
    ":rocket:": "\U0001f680",
    ":warning:": "\u26a0\ufe0f",
}

def _replace_emoji(text, default_variant=None):
    return re.sub(r":(\S+?):", lambda m: _EMOJI.get(m.group(0), m.group(0)), text)

# --- Core Classes ---

Segment = namedtuple("Segment", ["text", "style"])

class Text:
    def __init__(self, text="", style=None):
        self._text = ""
        self.spans = []
        if text:
            self.append(text, style)

    @classmethod
    def from_markup(cls, markup_text):
        text_obj = cls()
        style_stack = []
        
        parts = re.split(r'(\[.*?\])', markup_text)
        for part in parts:
            if not part:
                continue
            if part.startswith('[') and part.endswith(']'):
                tag = part[1:-1]
                if tag.startswith('/'):
                    if style_stack:
                        style_stack.pop()
                else:
                    style_stack.append(tag)
            else:
                current_style = " ".join(style_stack) if style_stack else None
                text_obj.append(part, style=current_style)
        return text_obj

    def __len__(self):
        return len(self._text)

    def __str__(self):
        return self._text

    def append(self, text, style=None):
        start = len(self._text)
        self._text += text
        end = len(self._text)
        if style:
            self.spans.append((start, end, style))

    def __rich_console__(self, console, options):
        plain_text = self._text
        if not self.spans:
            yield Segment(plain_text, None)
            return

        current_pos = 0
        for start, end, style in sorted(self.spans):
            if start > current_pos:
                yield Segment(plain_text[current_pos:start], None)
            yield Segment(plain_text[start:end], style)
            current_pos = end
        if current_pos < len(plain_text):
            yield Segment(plain_text[current_pos:], None)

class Console:
    def __init__(self, width=80, file=None):
        self.width = width
        self._file = file or sys.stdout

    def print(self, *objects, **kwargs):
        if not objects:
            self._file.write("\n")
            return
        
        for obj in objects:
            if isinstance(obj, str):
                obj = _replace_emoji(obj)
                obj = Text.from_markup(obj)

            if not hasattr(obj, "__rich_console__"):
                obj = Text(str(obj))

            for line in self._render_obj(obj):
                self._file.write(line + "\n")

    def _render_obj(self, obj):
        segments = list(obj.__rich_console__(self, self))
        lines_of_segments = self._wrap_segments(segments, self.width)
        
        output_lines = []
        for line_segments in lines_of_segments:
            line_str = ""
            for text, style in line_segments:
                if style:
                    line_str += _style_to_ansi(style) + text + _RESET
                else:
                    line_str += text
            output_lines.append(line_str)
        return output_lines

    @staticmethod
    def _wrap_segments(segments, max_width):
        lines = []
        current_line = []
        current_length = 0

        # First, split any segments that contain newlines
        split_segments = []
        for text, style in segments:
            parts = text.split('\n')
            for i, part in enumerate(parts):
                if part:
                    split_segments.append(Segment(part, style))
                if i < len(parts) - 1:
                    split_segments.append(Segment('\n', None))
        
        for text, style in split_segments:
            if text == '\n':
                lines.append(current_line)
                current_line = []
                current_length = 0
                continue

            words = re.split(r'(\s+)', text)
            for word in words:
                if not word:
                    continue
                word_len = len(word)

                if word_len > max_width:
                    if current_line:
                        lines.append(current_line)
                    for i in range(0, word_len, max_width):
                        lines.append([Segment(word[i:i+max_width], style)])
                    current_line = []
                    current_length = 0
                    continue

                if current_length > 0 and current_length + word_len > max_width:
                    lines.append(current_line)
                    current_line = []
                    current_length = 0
                
                if not current_line and word.isspace():
                    continue

                current_line.append(Segment(word, style))
                current_length += word_len

        if current_line:
            lines.append(current_line)

        merged_lines = []
        for line in lines:
            if not line:
                merged_lines.append([])
                continue
            
            merged_line = []
            current_text, current_style = line[0]
            for text, style in line[1:]:
                if style == current_style:
                    current_text += text
                else:
                    merged_line.append(Segment(current_text, current_style))
                    current_text, current_style = text, style
            merged_line.append(Segment(current_text, current_style))
            merged_lines.append(merged_line)
            
        return merged_lines