"""Text class for styled text."""

from typing import Optional, Union, List, Tuple, Any


class Text:
    """Text with styles."""

    def __init__(
        self,
        text: str = "",
        style: Optional[str] = None,
        *,
        justify: Optional[str] = None,
        overflow: Optional[str] = None,
        no_wrap: Optional[bool] = None,
        end: str = "\n",
        tab_size: Optional[int] = 8,
        spans: Optional[List[Any]] = None,
    ) -> None:
        self._text = text
        self.style = style
        self.justify = justify
        self.overflow = overflow
        self.no_wrap = no_wrap
        self.end = end
        self.tab_size = tab_size
        self.spans = spans or []

    @property
    def plain(self) -> str:
        """Get plain text without styles."""
        return self._text

    def __str__(self) -> str:
        """Return plain text."""
        return self._text

    def __repr__(self) -> str:
        """Return representation."""
        return f"Text({self._text!r}, {self.style!r})"

    def __len__(self) -> int:
        """Return length of text."""
        return len(self._text)

    def append(self, text: Union[str, "Text"], style: Optional[str] = None) -> "Text":
        """Append text."""
        if isinstance(text, Text):
            self._text += text._text
        else:
            self._text += str(text)
        return self

    def stylize(self, style: str, start: int = 0, end: Optional[int] = None) -> None:
        """Apply a style to a range of text."""
        if end is None:
            end = len(self._text)
        self.spans.append((start, end, style))

    @classmethod
    def from_markup(cls, text: str, *, style: Optional[str] = None, emoji: bool = True) -> "Text":
        """Create Text from markup."""
        import re
        
        # Remove markup tags
        plain_text = re.sub(r'\[/?[a-zA-Z0-9_\s#]+\]', '', text)
        
        # Process emoji if enabled
        if emoji:
            emoji_map = {
                ':smiley:': '😃',
                ':heart:': '❤️',
                ':thumbs_up:': '👍',
                ':rocket:': '🚀',
                ':fire:': '🔥',
                ':star:': '⭐',
                ':check_mark:': '✅',
                ':cross_mark:': '❌',
                ':warning:': '⚠️',
                ':sparkles:': '✨',
            }
            for code, emoji_char in emoji_map.items():
                plain_text = plain_text.replace(code, emoji_char)
        
        return cls(plain_text, style=style)

    def assemble(self, *parts: Union[str, Tuple[str, str]]) -> "Text":
        """Assemble text from parts."""
        for part in parts:
            if isinstance(part, tuple):
                text, style = part
                self.append(text, style)
            else:
                self.append(part)
        return self