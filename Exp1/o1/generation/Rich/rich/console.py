import sys
import re
from .text import Text
from .theme import Style
from .theme import Theme

COLOR_MAP = {
    "black": 30, "red": 31, "green": 32, "yellow": 33,
    "blue": 34, "magenta": 35, "cyan": 36, "white": 37,
    "bright_black": 90, "bright_red": 91, "bright_green": 92, "bright_yellow": 93,
    "bright_blue": 94, "bright_magenta": 95, "bright_cyan": 96, "bright_white": 97,
}

RESET_ALL = "\033[0m"

EMOJI_MAP = {
    ":smiley:": "😃",
    ":thumbs_up:": "👍",
    ":heart:": "❤️",
    ":star:": "⭐",
    ":check_mark:": "✔️",
}


def replace_emoji(text: str) -> str:
    """Replace known emoji placeholders with their unicode characters."""
    for placeholder, unicode_emoji in EMOJI_MAP.items():
        text = text.replace(placeholder, unicode_emoji)
    return text


def parse_color_markup(text: str, theme: Theme = None) -> str:
    """
    Naive color markup parser that interprets [color] as terminal color,
    and [/color] as reset.
    """
    # Stack to keep track of active color codes
    style_stack = []
    output = []
    # Tokenize by bracket-based markup
    # We'll match [something] tokens and treat them as style open/close
    idx = 0
    pattern = re.compile(r"(\[/?[a-z_]+\])")
    tokens = pattern.split(text)

    for token in tokens:
        if token.startswith("[") and token.endswith("]"):
            # It's a markup tag
            tag_content = token.strip("[]/")
            opening = not token.startswith("[/")
            if opening:
                # style name
                style_name = tag_content
                # check theme
                style_obj = None
                if theme:
                    style_obj = theme.styles.get(style_name, None)
                if style_obj:
                    # If there's a theme style, apply it
                    output.append(style_obj.to_ansi())
                    style_stack.append(style_obj)
                else:
                    # fallback to color
                    color_code = COLOR_MAP.get(style_name, None)
                    if color_code:
                        output.append(f"\033[{color_code}m")
                        style_stack.append(Style(color=style_name))
                    else:
                        # unrecognized tag
                        output.append(token)
            else:
                # closing tag
                if style_stack:
                    style_stack.pop()
                # revert to what's on top of the stack
                if style_stack:
                    top_style = style_stack[-1]
                    output.append(top_style.to_ansi())
                else:
                    # no styles in stack
                    output.append(RESET_ALL)
        else:
            # normal text
            output.append(token)

    return "".join(output)


def strip_color_markup(text: str) -> str:
    """Remove markup like [red], [/red], etc. for measuring display width."""
    return re.sub(r"\[/?[a-z_]+\]", "", text)


def wrap_text(text: str, width: int) -> str:
    """
    Very naive wrapping at space boundaries:
    Splits the text by spaces and rejoin lines with width limit.
    """
    words = text.split()
    wrapped_lines = []
    line = []
    current_length = 0
    for w in words:
        if current_length + len(w) + (len(line) > 0) <= width:
            line.append(w)
            current_length += len(w) + (1 if len(line) > 1 else 0)
        else:
            wrapped_lines.append(" ".join(line))
            line = [w]
            current_length = len(w)
    if line:
        wrapped_lines.append(" ".join(line))
    return "\n".join(wrapped_lines)


class Console:
    """
    A minimal Console, capable of printing Rich-like objects and handling markup.
    """

    def __init__(self, theme: Theme = None, width: int = 80, file=None):
        self.theme = theme
        self.width = width
        self.file = file if file is not None else sys.stdout

    def print(self, *objects, sep=" ", end="\n", style=None, emoji=True):
        """Print objects with optional color markup, styling, and emoji support."""
        to_print = []
        for obj in objects:
            lines = []
            if hasattr(obj, "__rich_console__"):
                # If it's a Rich-like object, ask it for lines
                for segment in obj.__rich_console__(self):
                    lines.append(segment)
            else:
                # Convert to string, possibly a Text object
                if isinstance(obj, Text):
                    s = obj.plain
                else:
                    s = str(obj)
                lines.append(s)

            # Flatten lines with sep
            to_print.append(sep.join(lines))

        printed = sep.join(to_print)
        if emoji:
            printed = replace_emoji(printed)
        if style:
            printed = f"[{style}]{printed}[/{style}]"
        # Now parse color markup
        printed_with_styles = parse_color_markup(printed, self.theme)
        # Potentially wrap
        if self.width > 0:
            # We handle each line separately for wrapping
            final_output = []
            for line in printed_with_styles.split("\n"):
                # But first let's remove markup for measuring length
                raw_line = strip_color_markup(line)
                if len(raw_line) > self.width:
                    # naive re-wrap the raw text, then reapply parse
                    wrapped_raw = wrap_text(raw_line, self.width)
                    # parse color markup after re-inserting markup? 
                    # We won't perfectly re-inject. We'll cheat and do no markup for wrapped lines.
                    # Real Rich does fancy per-word style tracking, but we'll keep it simple.
                    # We'll just parse the entire thing for the first line and then plain for extras.
                    first_line = True
                    for wline in wrapped_raw.split("\n"):
                        if first_line:
                            # keep original markup for the first line
                            final_output.append(parse_color_markup(wline, self.theme))
                            first_line = False
                        else:
                            final_output.append(wline)
                else:
                    final_output.append(line)
            printed_with_styles = "\n".join(final_output)

        self.file.write(printed_with_styles + end)
        self.file.flush()

    def rule(self, title: str = "", style: str = "rule"):
        """Print a horizontal rule with optional title."""
        raw_title = title
        if title:
            raw_title = f" {raw_title} "
        line_length = self.width - len(strip_color_markup(raw_title)) - 2
        if line_length < 1:
            line_length = 1
        bar = "─" * line_length
        self.print(f"[{style}]{bar}{raw_title}{bar}[/{style}]", emoji=False)