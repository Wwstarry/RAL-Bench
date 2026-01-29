"""Text with styling support."""

from typing import Optional, List, Tuple, Union, Any
from dataclasses import dataclass


@dataclass
class Span:
    """Represents a span of styled text."""

    start: int
    end: int
    style: str


class Text:
    """A string with optional styling."""

    def __init__(
        self,
        text: Union[str, "Text"] = "",
        style: Optional[str] = None,
        justify: Optional[str] = None,
        overflow: Optional[str] = None,
        no_wrap: bool = False,
        end: str = "\n",
        tab_size: int = 8,
        emoji: bool = True,
        markup: bool = True,
    ):
        """Initialize a Text instance."""
        if isinstance(text, Text):
            self.plain = text.plain
            self.spans = list(text.spans)
            self.style = style or text.style
        else:
            self.plain = str(text)
            self.spans: List[Span] = []
            if style:
                self.spans.append(Span(0, len(self.plain), style))
            self.style = style

        self.justify = justify
        self.overflow = overflow
        self.no_wrap = no_wrap
        self.end = end
        self.tab_size = tab_size
        self.emoji = emoji
        self.markup = markup

    def __str__(self) -> str:
        """Return the plain text."""
        return self.plain

    def __repr__(self) -> str:
        """Return a representation of the Text."""
        return f"Text({self.plain!r}, style={self.style!r})"

    def __len__(self) -> int:
        """Return the length of the text."""
        return len(self.plain)

    def __add__(self, other: Union[str, "Text"]) -> "Text":
        """Concatenate with another Text or string."""
        if isinstance(other, str):
            other = Text(other)

        result = Text(self.plain + other.plain)
        result.spans = list(self.spans)

        # Adjust spans from other
        offset = len(self.plain)
        for span in other.spans:
            result.spans.append(Span(span.start + offset, span.end + offset, span.style))

        return result

    def __radd__(self, other: Union[str, "Text"]) -> "Text":
        """Right-hand concatenation."""
        if isinstance(other, str):
            other = Text(other)
        return other.__add__(self)

    def append(self, text: Union[str, "Text"], style: Optional[str] = None) -> "Text":
        """Append text to this Text."""
        if isinstance(text, str):
            text = Text(text, style=style)

        self.plain += text.plain
        offset = len(self.plain) - len(text.plain)

        for span in text.spans:
            self.spans.append(Span(span.start + offset, span.end + offset, span.style))

        if style and not text.spans:
            self.spans.append(Span(offset, len(self.plain), style))

        return self

    def stylize(self, style: str, start: int = 0, end: Optional[int] = None) -> "Text":
        """Apply a style to a range of text."""
        if end is None:
            end = len(self.plain)

        self.spans.append(Span(start, end, style))
        return self

    def stylize_before(self, style: str, start: int = 0, end: Optional[int] = None) -> "Text":
        """Apply a style before other spans."""
        if end is None:
            end = len(self.plain)

        self.spans.insert(0, Span(start, end, style))
        return self

    def assemble(self, *parts: Union[str, "Text", Tuple[str, str]]) -> "Text":
        """Assemble text from parts."""
        for part in parts:
            if isinstance(part, tuple):
                text, style = part
                self.append(text, style=style)
            else:
                self.append(part)
        return self

    def split(self, separator: str = "\n") -> List["Text"]:
        """Split text by separator."""
        parts = self.plain.split(separator)
        result = []

        pos = 0
        for part in parts:
            text = Text(part)
            # Apply relevant spans
            for span in self.spans:
                if span.start < pos + len(part) and span.end > pos:
                    start = max(0, span.start - pos)
                    end = min(len(part), span.end - pos)
                    if start < end:
                        text.spans.append(Span(start, end, span.style))
            result.append(text)
            pos += len(part) + len(separator)

        return result

    def __rich_console__(self, console: Any, options: Any) -> str:
        """Render the text for console output."""
        return self.plain

    def __rich__(self) -> str:
        """Return rich representation."""
        return self.plain