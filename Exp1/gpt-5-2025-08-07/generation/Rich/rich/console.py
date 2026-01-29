import io
import os
import re
import sys
import shutil
import textwrap
from typing import Any, Iterable, Optional

# Minimal emoji map used for tests
_EMOJI_MAP = {
    "smile": "😄",
    "warning": "⚠️",
    "rocket": "🚀",
    "hourglass": "⌛",
    "hourglass_flowing_sand": "⏳",
    "heavy_check_mark": "✔️",
    "white_check_mark": "✅",
    "x": "✖",
    "sparkles": "✨",
    "sunny": "☀️",
    "tada": "🎉",
    "star": "⭐",
    "fire": "🔥",
    "snake": "🐍",
    "ok": "🆗",
    "information_source": "ℹ️",
    "bulb": "💡",
    "check_mark": "✔",
    "cross_mark": "❌",
}


_ALLOWED_MARKUP = {
    "b",
    "bold",
    "i",
    "italic",
    "u",
    "underline",
    "dim",
    "reverse",
    "strike",
    "blink",
    "red",
    "green",
    "blue",
    "yellow",
    "magenta",
    "cyan",
    "white",
    "black",
    "/",
    "/b",
    "/bold",
    "/i",
    "/italic",
    "/u",
    "/underline",
    "/dim",
    "/reverse",
    "/strike",
    "/blink",
}


def _supports_color(stream: io.TextIOBase) -> bool:
    if not hasattr(stream, "isatty"):
        return False
    try:
        return bool(stream.isatty())
    except Exception:
        return False


def _get_terminal_width(default: int = 80) -> int:
    try:
        size = shutil.get_terminal_size(fallback=(default, 25))
        return int(size.columns)
    except Exception:
        return default


def _replace_emoji(text: str) -> str:
    def repl(m: re.Match) -> str:
        name = m.group(1)
        return _EMOJI_MAP.get(name, m.group(0))
    return re.sub(r":([a-z0-9_\-\+]+):", repl, text)


def _strip_markup(text: str) -> str:
    if not text:
        return text

    # Handle escaped brackets first: [[ -> literal [, ]] -> literal ]
    placeholder_l = "\u0000"
    placeholder_r = "\u0001"
    text = text.replace("[[", placeholder_l).replace("]]", placeholder_r)

    # Remove supported markup tags, keep unknown tags untouched
    # Support color like #RRGGBB
    def tag_repl(m: re.Match) -> str:
        inner = m.group(1).strip()
        # Hex color or hex + style like "#ff00aa bold"
        if inner.startswith("#"):
            return ""  # remove but ignore attributes
        if inner in _ALLOWED_MARKUP:
            return ""
        # supports style=... like "bold red"
        # If all parts are allowed, strip; otherwise keep
        parts = inner.split()
        if parts and all((p in _ALLOWED_MARKUP or p.startswith("#")) for p in parts):
            return ""
        # opening/closing tags can be "style=..." or "link=..." etc; strip simple "style="
        if inner.startswith("style="):
            return ""
        if inner == "/style":
            return ""
        if inner == "/":
            return ""
        # Unknown tag, keep original
        return m.group(0)

    text = re.sub(r"\[([^\[\]]+)\]", tag_repl, text)

    # restore escaped brackets
    return text.replace(placeholder_l, "[").replace(placeholder_r, "]")


class Console:
    def __init__(
        self,
        file: Optional[io.TextIOBase] = None,
        force_terminal: Optional[bool] = None,
        width: Optional[int] = None,
        markup: bool = True,
        emoji: bool = True,
        record: bool = False,
        color_system: Optional[str] = None,
        soft_wrap: bool = False,
    ) -> None:
        self.file = file if file is not None else sys.stdout
        self._force_terminal = force_terminal
        self._width = width
        self.markup = markup
        self.emoji = emoji
        self.record = record
        self.color_system = color_system
        self.soft_wrap = soft_wrap
        self._buffer: Optional[io.StringIO] = io.StringIO() if record else None
        # Color support detection; we don't actually emit ANSI in this implementation.
        self._is_terminal = True if force_terminal else _supports_color(self.file)

    @property
    def width(self) -> int:
        if self._width is not None:
            return int(self._width)
        return _get_terminal_width()

    def _render_object(self, obj: Any) -> str:
        # Text-like object
        # Prefer a duck-typed .render(width=..) if present for Rich-like renderables
        if hasattr(obj, "render"):
            try:
                return obj.render(self.width)  # type: ignore
            except TypeError:
                # .render without width
                try:
                    return obj.render()  # type: ignore
                except Exception:
                    pass
        if hasattr(obj, "__rich__"):
            try:
                rich_text = obj.__rich__()  # type: ignore
                if isinstance(rich_text, str):
                    return rich_text
            except Exception:
                pass
        if hasattr(obj, "__str__"):
            return str(obj)
        return repr(obj)

    def _process_text(self, text: str, wrap: bool = True) -> str:
        out = text
        if self.markup:
            out = _strip_markup(out)
        if self.emoji:
            out = _replace_emoji(out)
        # Normalize CRLF
        out = out.replace("\r\n", "\n").replace("\r", "\n")
        if wrap and not self.soft_wrap and self.width and self.width > 0:
            new_lines: list[str] = []
            for line in out.split("\n"):
                if not line:
                    new_lines.append("")
                    continue
                wrapped = textwrap.wrap(
                    line,
                    width=self.width,
                    break_long_words=True,
                    break_on_hyphens=True,
                    replace_whitespace=False,
                    drop_whitespace=False,
                )
                if not wrapped:
                    new_lines.append("")
                else:
                    new_lines.extend(wrapped)
            out = "\n".join(new_lines)
        return out

    def print(self, *objects: Any, sep: str = " ", end: str = "\n", flush: bool = False) -> None:
        parts: list[str] = []
        for obj in objects:
            s = self._render_object(obj)
            # If the object appears to be a pre-rendered block (like a table/progress),
            # we avoid additional wrapping to preserve layout.
            wrap = True
            if "\n" in s and hasattr(obj, "render"):
                wrap = False
            s = self._process_text(s, wrap=wrap)
            parts.append(s)
        text = sep.join(parts) + end
        try:
            self.file.write(text)
        except Exception:
            # Best-effort fallback: encode errors ignored
            self.file.write(text.encode("utf-8", "ignore").decode("utf-8", "ignore"))
        if self._buffer is not None:
            self._buffer.write(text)
        if flush:
            try:
                self.file.flush()
            except Exception:
                pass

    def capture(self) -> "ConsoleCapture":
        return ConsoleCapture(self)

    # Compatibility helpers
    def rule(self, title: str = "", characters: str = "─") -> None:
        line_width = max(0, self.width)
        if title:
            title_proc = self._process_text(title, wrap=False)
            # Ensure title is surrounded by spaces
            core = f" {title_proc} "
            rem = max(0, line_width - len(core))
            left = rem // 2
            right = rem - left
            s = characters * left + core + characters * right
        else:
            s = characters * line_width
        self.print(s)

    def clear(self) -> None:
        # No-op clear; just print a newline for compatibility
        self.print("")

    def export_text(self) -> str:
        if self._buffer is None:
            return ""
        return self._buffer.getvalue()


class ConsoleCapture:
    def __init__(self, console: Console) -> None:
        self.console = console
        self._prev_buffer = console._buffer
        self._buffer = io.StringIO()

    def __enter__(self) -> "ConsoleCapture":
        self.console._buffer = self._buffer
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.console._buffer = self._prev_buffer

    def get(self) -> str:
        return self._buffer.getvalue()