import re
from typing import List, Tuple, Union

class Text:
    def __init__(self, text: str = "", style: str = ""):
        self._spans: List[Tuple[str, str]] = []
        if text:
            self.append(text, style)

    def append(self, text: str, style: str = ""):
        if text:
            self._spans.append((text, style))

    @property
    def plain(self) -> str:
        return "".join(text for text, _ in self._spans)

    def __len__(self):
        return len(self.plain)

    def __str__(self):
        return self.plain

    def __rich_console__(self, console, options):
        # Basic ANSI rendering
        output = []
        for text, style in self._spans:
            ansi_codes = []
            if style:
                # Very basic style parser for the sake of the exercise
                parts = style.split()
                for part in parts:
                    if part == "bold":
                        ansi_codes.append("1")
                    elif part == "italic":
                        ansi_codes.append("3")
                    elif part == "red":
                        ansi_codes.append("31")
                    elif part == "green":
                        ansi_codes.append("32")
                    elif part == "blue":
                        ansi_codes.append("34")
                    elif part == "yellow":
                        ansi_codes.append("33")
                    elif part == "magenta":
                        ansi_codes.append("35")
                    elif part == "cyan":
                        ansi_codes.append("36")
                    elif part == "white":
                        ansi_codes.append("37")
            
            if ansi_codes:
                output.append(f"\033[{';'.join(ansi_codes)}m{text}\033[0m")
            else:
                output.append(text)
        yield "".join(output)

    @classmethod
    def from_markup(cls, text: str, style: str = "") -> "Text":
        # Simplified markup parser: [style]text[/] or [style]text[/style]
        # This is a naive implementation for the exercise
        instance = cls(style=style)
        # Regex to find tags
        parts = re.split(r'(\[.*?\])', text)
        current_style = style
        stack = [style]

        for part in parts:
            if part.startswith("[") and part.endswith("]"):
                tag = part[1:-1]
                if tag.startswith("/"):
                    if len(stack) > 1:
                        stack.pop()
                    current_style = stack[-1]
                else:
                    # simplistic style merge
                    current_style = f"{current_style} {tag}".strip()
                    stack.append(current_style)
            else:
                instance.append(part, current_style)
        return instance