import sys
import os
import re
from typing import Optional, List, Any, Union, TextIO, Callable
from dataclasses import dataclass, field
from enum import Enum

from rich.text import Text
from rich.theme import Theme


class ColorSystem(Enum):
    """Color system supported by the terminal."""
    STANDARD = 1
    EIGHT_BIT = 2
    TRUECOLOR = 3
    NONE = 0


@dataclass
class ConsoleOptions:
    """Options for console rendering."""
    max_width: Optional[int] = None
    min_width: int = 1
    color_system: Optional[ColorSystem] = None
    legacy_windows: bool = False
    safe_box: bool = True
    markup: bool = True
    emoji: bool = True
    highlight: bool = True
    soft_wrap: bool = False


class Console:
    """A console for rich text output."""
    
    def __init__(
        self,
        *,
        color_system: Optional[str] = None,
        force_terminal: Optional[bool] = None,
        force_jupyter: Optional[bool] = None,
        force_interactive: Optional[bool] = None,
        soft_wrap: bool = False,
        theme: Optional[Theme] = None,
        stderr: bool = False,
        file: Optional[TextIO] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        markup: bool = True,
        emoji: bool = True,
        highlight: bool = True,
        legacy_windows: Optional[bool] = None,
        safe_box: bool = True,
    ):
        self._theme = theme or Theme.default()
        self._width = width
        self._height = height
        self.markup = markup
        self.emoji = emoji
        self.highlight = highlight
        self.safe_box = safe_box
        self.soft_wrap = soft_wrap
        
        # Determine file
        if file is not None:
            self.file = file
        elif stderr:
            self.file = sys.stderr
        else:
            self.file = sys.stdout
            
        # Determine color system
        if color_system is None:
            self.color_system = self._detect_color_system()
        else:
            color_system = color_system.upper()
            if color_system == "STANDARD":
                self.color_system = ColorSystem.STANDARD
            elif color_system == "EIGHT_BIT":
                self.color_system = ColorSystem.EIGHT_BIT
            elif color_system == "TRUECOLOR":
                self.color_system = ColorSystem.TRUECOLOR
            elif color_system == "NONE":
                self.color_system = ColorSystem.NONE
            else:
                self.color_system = ColorSystem.STANDARD
                
        # Legacy Windows
        if legacy_windows is None:
            self.legacy_windows = sys.platform == "win32" and not self._windows_ansi_support()
        else:
            self.legacy_windows = legacy_windows
            
        self._options = ConsoleOptions(
            max_width=self.width,
            min_width=1,
            color_system=self.color_system,
            legacy_windows=self.legacy_windows,
            safe_box=self.safe_box,
            markup=self.markup,
            emoji=self.emoji,
            highlight=self.highlight,
            soft_wrap=self.soft_wrap,
        )
        
    @property
    def width(self) -> int:
        """Get the width of the console."""
        if self._width is not None:
            return self._width
            
        try:
            return os.get_terminal_size().columns
        except (OSError, AttributeError):
            return 80
            
    @property
    def height(self) -> int:
        """Get the height of the console."""
        if self._height is not None:
            return self._height
            
        try:
            return os.get_terminal_size().lines
        except (OSError, AttributeError):
            return 24
            
    def _detect_color_system(self) -> ColorSystem:
        """Detect the color system supported by the terminal."""
        # Check environment variables
        color_term = os.environ.get("COLORTERM", "")
        term = os.environ.get("TERM", "")
        
        if color_term in ("truecolor", "24bit"):
            return ColorSystem.TRUECOLOR
        elif "256color" in term:
            return ColorSystem.EIGHT_BIT
        elif "color" in term or "ansi" in term:
            return ColorSystem.STANDARD
        else:
            return ColorSystem.NONE
            
    def _windows_ansi_support(self) -> bool:
        """Check if Windows supports ANSI escape codes."""
        if sys.platform != "win32":
            return True
            
        # Windows 10+ supports ANSI
        import platform
        version = platform.version()
        if version:
            major = int(version.split('.')[0])
            return major >= 10
        return False
        
    def print(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Print to the console."""
        text_parts = []
        
        for obj in objects:
            if isinstance(obj, str):
                if self.markup:
                    text = self._render_markup(obj)
                else:
                    text = Text(obj)
            elif isinstance(obj, Text):
                text = obj
            else:
                text = Text(str(obj))
                
            if style:
                text.stylize(style)
                
            text_parts.append(text)
            
        if not text_parts:
            output = Text()
        elif len(text_parts) == 1:
            output = text_parts[0]
        else:
            output = Text()
            for i, text in enumerate(text_parts):
                if i > 0:
                    output.append(sep)
                output.append(text)
                
        # Render and write
        rendered = self._render_text(output)
        self.file.write(rendered + end)
        self.file.flush()
        
    def _render_markup(self, markup: str) -> Text:
        """Render markup string to Text."""
        text = Text()
        buffer = []
        in_tag = False
        tag_content = []
        
        i = 0
        while i < len(markup):
            char = markup[i]
            
            if char == '[' and not in_tag:
                # Check if it's a tag
                if i + 1 < len(markup) and markup[i + 1] != '[':
                    # Start of tag
                    in_tag = True
                    if buffer:
                        text.append(''.join(buffer))
                        buffer.clear()
                    i += 1
                    continue
                else:
                    # Escaped '['
                    buffer.append('[')
                    i += 2 if i + 1 < len(markup) else 1
                    continue
                    
            elif char == ']' and in_tag:
                # End of tag
                in_tag = False
                tag = ''.join(tag_content)
                tag_content.clear()
                
                # Parse tag
                if tag.startswith('/'):
                    # Closing tag
                    pass  # Simple implementation - ignore closing tags
                else:
                    # Opening tag
                    if ' ' in tag:
                        tag_name, tag_rest = tag.split(' ', 1)
                    else:
                        tag_name, tag_rest = tag, ''
                        
                    # Apply style
                    style = self._theme.get(tag_name, tag_name)
                    if buffer:
                        text.append(''.join(buffer), style=style)
                        buffer.clear()
                        
                i += 1
                continue
                
            if in_tag:
                tag_content.append(char)
            else:
                buffer.append(char)
                
            i += 1
            
        if buffer:
            text.append(''.join(buffer))
            
        return text
        
    def _render_text(self, text: Text) -> str:
        """Render Text object to string with escape codes."""
        if self.color_system == ColorSystem.NONE or self.legacy_windows:
            return text.plain
            
        result = []
        current_style = None
        
        for segment in text._segments:
            content, style = segment
            
            if style != current_style:
                if current_style is not None:
                    result.append('\033[0m')
                if style:
                    result.append(self._style_to_ansi(style))
                current_style = style
                
            result.append(content)
            
        if current_style is not None:
            result.append('\033[0m')
            
        return ''.join(result)
        
    def _style_to_ansi(self, style: str) -> str:
        """Convert style string to ANSI escape codes."""
        codes = []
        
        # Parse style components
        components = style.split()
        for comp in components:
            if comp in self._theme:
                # Recursively resolve theme
                codes.extend(self._style_to_ansi(self._theme[comp]).strip('\033[').strip('m').split(';'))
            elif comp.startswith('#'):
                # RGB color
                if len(comp) == 7:  # #RRGGBB
                    r = int(comp[1:3], 16)
                    g = int(comp[3:5], 16)
                    b = int(comp[5:7], 16)
                    if self.color_system == ColorSystem.TRUECOLOR:
                        codes.extend(['38', '2', str(r), str(g), str(b)])
                    else:
                        # Approximate to 256 colors
                        codes.append(str(self._rgb_to_ansi256(r, g, b) + 16))
            elif comp in self._COLOR_MAP:
                codes.append(self._COLOR_MAP[comp])
            elif comp in self._STYLE_MAP:
                codes.append(self._STYLE_MAP[comp])
                
        return f'\033[{";".join(codes)}m' if codes else ''
        
    def _rgb_to_ansi256(self, r: int, g: int, b: int) -> int:
        """Convert RGB to 256-color ANSI code."""
        # Simple approximation
        if r == g == b:
            if r < 8:
                return 16
            elif r > 248:
                return 231
            else:
                return int(((r - 8) / 247) * 24) + 232
                
        # Color cube
        return (
            16 +
            36 * int(r / 255 * 5) +
            6 * int(g / 255 * 5) +
            int(b / 255 * 5)
        )
        
    _COLOR_MAP = {
        'black': '30',
        'red': '31',
        'green': '32',
        'yellow': '33',
        'blue': '34',
        'magenta': '35',
        'cyan': '36',
        'white': '37',
        'bright_black': '90',
        'bright_red': '91',
        'bright_green': '92',
        'bright_yellow': '93',
        'bright_blue': '94',
        'bright_magenta': '95',
        'bright_cyan': '96',
        'bright_white': '97',
    }
    
    _STYLE_MAP = {
        'bold': '1',
        'dim': '2',
        'italic': '3',
        'underline': '4',
        'blink': '5',
        'reverse': '7',
        'conceal': '8',
        'strike': '9',
    }