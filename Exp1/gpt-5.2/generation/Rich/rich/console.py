from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Optional, Sequence, TextIO, Union

from .text import Text
from .theme import Theme
from ._emoji import emojize
from ._wrap import wrap_lines
from ._ansi import strip_ansi, render_ansi_from_style


RenderableType = Any


_TAG_RE = re.compile(r"\[(/?)([a-zA-Z0-9_\-]+)(?:=([^\]]+))?\]")


def _parse_markup_to_ansi(text: str) -> str:
    """
    Very small subset of Rich markup:
    - [bold], [italic], [underline], [reverse]
    - [color], [color=...], [/]
    - [/] closes last style
    - [reset] resets all styles
    This is intentionally minimal.
    """
    stack: List[str] = []
    out: List[str] = []
    pos = 0
    for m in _TAG_RE.finditer(text):
        out.append(text[pos : m.start()])
        pos = m.end()
        closing = bool(m.group(1))
        tag = (m.group(2) or "").lower()
        value = m.group(3)

        if tag == "reset":
            stack.clear()
            out.append("\x1b[0m")
            continue

        if closing:
            if tag in ("", None) or tag == "/":
                # [/]
                if stack:
                    stack.pop()
                out.append("\x1b[0m" + "".join(render_ansi_from_style(s) for s in stack))
            else:
                # [/tag]
                # remove last occurrence of tag-like entries
                for i in range(len(stack) - 1, -1, -1):
                    if stack[i] == tag or stack[i].startswith(tag + "="):
                        stack.pop(i)
                        break
                out.append("\x1b[0m" + "".join(render_ansi_from_style(s) for s in stack))
            continue

        # opening
        style = tag if value is None else f"{tag}={value}"
        stack.append(style)
        out.append(render_ansi_from_style(style))

    out.append(text[pos:])
    if stack:
        out.append("\x1b[0m")
    return "".join(out)


def _coerce_renderable(obj: Any) -> Text:
    if obj is None:
        return Text("")
    if isinstance(obj, Text):
        return obj
    if hasattr(obj, "__rich_console__"):
        # minimal protocol: return iterable of Text/str
        # We'll join into Text lines
        parts: List[str] = []
        for part in obj.__rich_console__(Console(), ConsoleOptions()):  # type: ignore
            if isinstance(part, Text):
                parts.append(part.plain)
            else:
                parts.append(str(part))
        return Text("".join(parts))
    if hasattr(obj, "__rich__"):
        try:
            r = obj.__rich__()  # type: ignore
            return _coerce_renderable(r)
        except Exception:
            pass
    return Text(str(obj))


@dataclass
class ConsoleOptions:
    width: Optional[int] = None


class Console:
    def __init__(
        self,
        file: Optional[TextIO] = None,
        *,
        width: Optional[int] = None,
        color_system: Optional[str] = "auto",
        force_terminal: Optional[bool] = None,
        no_color: Optional[bool] = None,
        markup: bool = True,
        emoji: bool = True,
        theme: Optional[Theme] = None,
        soft_wrap: bool = False,
        record: bool = False,
    ) -> None:
        self.file: TextIO = file if file is not None else sys.stdout
        self._width = width
        self.color_system = color_system
        self.force_terminal = force_terminal
        self.no_color = bool(no_color) if no_color is not None else False
        self.markup = markup
        self.emoji = emoji
        self.theme = theme or Theme()
        self.soft_wrap = soft_wrap
        self.record = record
        self._record_buffer: List[str] = []

    @property
    def width(self) -> int:
        if self._width is not None:
            return self._width
        try:
            return os.get_terminal_size(getattr(self.file, "fileno", lambda: 1)()).columns
        except Exception:
            return 80

    def begin_capture(self) -> None:
        self.record = True
        self._record_buffer = []

    def end_capture(self) -> str:
        out = "".join(self._record_buffer)
        self.record = False
        self._record_buffer = []
        return out

    def _write(self, s: str) -> None:
        if self.record:
            self._record_buffer.append(s)
        else:
            self.file.write(s)
            try:
                self.file.flush()
            except Exception:
                pass

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
        soft_wrap: Optional[bool] = None,
    ) -> None:
        text = sep.join(_coerce_renderable(obj).plain for obj in objects)
        if emoji is None:
            emoji = self.emoji
        if markup is None:
            markup = self.markup
        if emoji:
            text = emojize(text)
        if style:
            # Wrap whole text in style
            if markup:
                text = f"[{style}]{text}[/]"
            else:
                # if no markup, still allow ANSI if terminal
                pass

        if markup:
            rendered = _parse_markup_to_ansi(text) if not self.no_color else strip_ansi(_parse_markup_to_ansi(text))
        else:
            rendered = text

        do_soft = self.soft_wrap if soft_wrap is None else bool(soft_wrap)
        if not do_soft:
            wrapped = wrap_lines(rendered, self.width)
            rendered = "\n".join(wrapped)

        self._write(rendered + end)

    def rule(self, title: str = "", *, style: str = "rule") -> None:
        w = self.width
        if title:
            label = f" {title} "
            fill = max(0, w - len(strip_ansi(label)))
            left = fill // 2
            right = fill - left
            line = "─" * left + label + "─" * right
        else:
            line = "─" * w
        if self.markup and not self.no_color:
            line = _parse_markup_to_ansi(f"[{style}]{line}[/]")
        self.print(line, markup=False)

    def render_str(self, text: str, *, markup: Optional[bool] = None, emoji: Optional[bool] = None) -> str:
        if emoji is None:
            emoji = self.emoji
        if markup is None:
            markup = self.markup
        if emoji:
            text = emojize(text)
        if markup:
            text = _parse_markup_to_ansi(text)
            if self.no_color:
                text = strip_ansi(text)
        return text

    def capture(self) -> "Capture":
        return Capture(self)

    def __rich_console__(self, console: "Console", options: ConsoleOptions) -> Iterable[Text]:
        yield Text("Console()")


class Capture:
    def __init__(self, console: Console) -> None:
        self.console = console
        self._active = False

    def __enter__(self) -> "Capture":
        self.console.begin_capture()
        self._active = True
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._active = False

    def get(self) -> str:
        return self.console.end_capture()