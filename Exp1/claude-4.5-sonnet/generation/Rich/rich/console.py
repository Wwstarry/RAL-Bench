"""Console class for rich terminal output."""

import sys
import re
from typing import Any, Optional, IO, Union, List, Tuple
from io import StringIO

from .text import Text
from .theme import Theme


class Console:
    """A high-level console interface."""

    def __init__(
        self,
        *,
        file: Optional[IO[str]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        force_terminal: Optional[bool] = None,
        force_jupyter: Optional[bool] = None,
        force_interactive: Optional[bool] = None,
        color_system: Optional[str] = "auto",
        legacy_windows: Optional[bool] = None,
        safe_box: bool = True,
        get_datetime: Optional[Any] = None,
        get_time: Optional[Any] = None,
        tab_size: int = 8,
        record: bool = False,
        markup: bool = True,
        emoji: bool = True,
        emoji_variant: Optional[str] = None,
        highlight: bool = True,
        log_time: bool = True,
        log_path: bool = True,
        log_time_format: str = "[%X]",
        highlighter: Optional[Any] = None,
        theme: Optional[Theme] = None,
        stderr: bool = False,
        style: Optional[str] = None,
        soft_wrap: bool = False,
        no_color: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        self.file = file or (sys.stderr if stderr else sys.stdout)
        self._width = width or 80
        self._height = height or 25
        self.legacy_windows = legacy_windows or False
        self.safe_box = safe_box
        self.tab_size = tab_size
        self.record = record
        self.markup = markup
        self.emoji = emoji
        self.emoji_variant = emoji_variant
        self.highlight = highlight
        self.log_time = log_time
        self.log_path = log_path
        self.log_time_format = log_time_format
        self.theme = theme or Theme()
        self.soft_wrap = soft_wrap
        self._recorded_output: List[str] = []
        self.color_system = color_system
        self.no_color = no_color

    @property
    def width(self) -> int:
        """Get the width of the console."""
        return self._width

    @property
    def height(self) -> int:
        """Get the height of the console."""
        return self._height

    def print(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[str] = None,
        justify: Optional[str] = None,
        overflow: Optional[str] = None,
        no_wrap: Optional[bool] = None,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: bool = True,
        soft_wrap: Optional[bool] = None,
        new_line_start: bool = False,
    ) -> None:
        """Print to the console."""
        use_markup = markup if markup is not None else self.markup
        use_emoji = emoji if emoji is not None else self.emoji
        
        output_parts = []
        for obj in objects:
            if isinstance(obj, Text):
                text = obj.plain
            elif hasattr(obj, "__rich__"):
                # Handle renderable objects
                rendered = self._render_str(obj)
                output_parts.append(rendered)
                continue
            else:
                text = str(obj)
            
            # Process markup
            if use_markup:
                text = self._process_markup(text)
            
            # Process emoji
            if use_emoji:
                text = self._process_emoji(text)
            
            output_parts.append(text)
        
        output = sep.join(output_parts) + end
        
        if self.record:
            self._recorded_output.append(output)
        
        self.file.write(output)
        self.file.flush()

    def _process_markup(self, text: str) -> str:
        """Process markup tags in text."""
        # Remove markup tags like [bold], [red], etc.
        text = re.sub(r'\[/?[a-zA-Z0-9_\s#]+\]', '', text)
        return text

    def _process_emoji(self, text: str) -> str:
        """Process emoji codes in text."""
        # Convert :emoji_name: to actual emoji
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
        for code, emoji in emoji_map.items():
            text = text.replace(code, emoji)
        return text

    def _render_str(self, obj: Any) -> str:
        """Render an object to string."""
        if hasattr(obj, "__rich_console__"):
            # Capture output from rich renderables
            buffer = StringIO()
            temp_console = Console(file=buffer, width=self.width)
            obj.__rich_console__(temp_console, None)
            return buffer.getvalue()
        return str(obj)

    def export_text(self, *, clear: bool = True, styles: bool = False) -> str:
        """Export recorded text."""
        output = "".join(self._recorded_output)
        if clear:
            self._recorded_output.clear()
        return output

    def rule(
        self,
        title: str = "",
        *,
        characters: str = "─",
        style: Union[str, Any] = "rule.line",
        align: str = "center",
    ) -> None:
        """Draw a horizontal rule."""
        if title:
            title_len = len(title)
            if align == "center":
                left_len = (self.width - title_len - 2) // 2
                right_len = self.width - title_len - 2 - left_len
                line = characters * left_len + " " + title + " " + characters * right_len
            elif align == "left":
                line = title + " " + characters * (self.width - title_len - 1)
            else:  # right
                line = characters * (self.width - title_len - 1) + " " + title
        else:
            line = characters * self.width
        
        self.print(line)

    def log(self, *objects: Any, **kwargs: Any) -> None:
        """Log output with optional timestamp."""
        self.print(*objects, **kwargs)