"""Console output and rendering."""

import sys
import re
from typing import Optional, Union, Any, List, TextIO
from io import StringIO


class Console:
    """A console for rendering rich content."""

    def __init__(
        self,
        file: Optional[TextIO] = None,
        width: Optional[int] = None,
        legacy_windows: bool = False,
        force_terminal: Optional[bool] = None,
        force_jupyter: bool = False,
        force_interactive: Optional[bool] = None,
        soft_wrap: bool = False,
        theme: Optional[Any] = None,
        stderr: bool = False,
        record: bool = False,
        markup: bool = True,
        emoji: bool = True,
        highlight: bool = True,
        log_time: bool = True,
        log_path: bool = True,
        _environ: Optional[dict] = None,
    ):
        """Initialize a Console instance."""
        self.file = file or (sys.stderr if stderr else sys.stdout)
        self.width = width or 80
        self.legacy_windows = legacy_windows
        self.force_terminal = force_terminal
        self.force_jupyter = force_jupyter
        self.force_interactive = force_interactive
        self.soft_wrap = soft_wrap
        self.theme = theme
        self.stderr = stderr
        self.record = record
        self.markup = markup
        self.emoji = emoji
        self.highlight = highlight
        self.log_time = log_time
        self.log_path = log_path
        self._record_buffer: List[str] = []
        self._environ = _environ or {}

    def print(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[str] = None,
        justify: Optional[str] = None,
        overflow: Optional[str] = None,
        no_wrap: bool = False,
        emoji: Optional[bool] = None,
        markup: Optional[bool] = None,
        highlight: Optional[bool] = None,
        soft_wrap: Optional[bool] = None,
        crop: bool = True,
    ) -> None:
        """Print objects to the console."""
        use_markup = markup if markup is not None else self.markup
        use_emoji = emoji if emoji is not None else self.emoji

        # Convert objects to strings
        parts = []
        for obj in objects:
            if hasattr(obj, "__rich__"):
                parts.append(obj.__rich__())
            elif hasattr(obj, "__rich_console__"):
                parts.append(obj.__rich_console__(self, None))
            else:
                parts.append(str(obj))

        text = sep.join(parts)

        # Process markup if enabled
        if use_markup:
            text = self._process_markup(text)

        # Process emoji if enabled
        if use_emoji:
            text = self._process_emoji(text)

        # Write to file
        output = text + end
        self.file.write(output)
        self.file.flush()

        # Record if enabled
        if self.record:
            self._record_buffer.append(output)

    def _process_markup(self, text: str) -> str:
        """Process markup tags in text."""
        # Simple markup processing for [color]text[/color] style tags
        # This is a basic implementation
        def replace_markup(match):
            tag = match.group(1)
            content = match.group(2)
            # For now, just return the content without ANSI codes
            # A full implementation would add ANSI escape sequences
            return content

        # Match [tag]content[/tag] patterns
        text = re.sub(r'\[([^\]]+)\]([^\[]*)\[/\1\]', replace_markup, text)
        # Match [tag]content[/] patterns
        text = re.sub(r'\[([^\]]+)\]([^\[]*)\[/\]', replace_markup, text)
        return text

    def _process_emoji(self, text: str) -> str:
        """Process emoji in text."""
        # Basic emoji processing - just return as-is for now
        return text

    def render(self, renderable: Any, options: Optional[Any] = None) -> str:
        """Render a renderable object to a string."""
        if hasattr(renderable, "__rich_console__"):
            return renderable.__rich_console__(self, options)
        return str(renderable)

    def export_text(self, clear: bool = True) -> str:
        """Export recorded text."""
        text = "".join(self._record_buffer)
        if clear:
            self._record_buffer.clear()
        return text

    def export_html(self, clear: bool = True, inline: bool = False) -> str:
        """Export recorded content as HTML."""
        text = "".join(self._record_buffer)
        if clear:
            self._record_buffer.clear()
        return text

    def rule(
        self,
        title: str = "",
        style: Optional[str] = None,
        align: str = "center",
        characters: str = "─",
    ) -> None:
        """Draw a rule."""
        if title:
            if align == "center":
                left_width = (self.width - len(title) - 2) // 2
                right_width = self.width - len(title) - 2 - left_width
                line = characters * left_width + " " + title + " " + characters * right_width
            elif align == "left":
                line = title + " " + characters * (self.width - len(title) - 1)
            else:  # right
                line = characters * (self.width - len(title) - 1) + " " + title
        else:
            line = characters * self.width

        self.print(line, style=style)

    def is_terminal(self) -> bool:
        """Check if the console is a terminal."""
        if self.force_terminal is not None:
            return self.force_terminal
        return hasattr(self.file, "isatty") and self.file.isatty()

    def get_width(self) -> int:
        """Get the console width."""
        return self.width

    def get_height(self) -> int:
        """Get the console height."""
        return 24  # Default height

    def set_width(self, width: int) -> None:
        """Set the console width."""
        self.width = width

    def clear(self) -> None:
        """Clear the console."""
        self.file.write("\033[2J\033[H")
        self.file.flush()