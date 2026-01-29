import sys
from typing import Any, IO, Optional
from .text import Text
from .theme import Theme

class Console:
    def __init__(self, file: IO = None, theme: Theme = None, width: int = 80):
        self.file = file or sys.stdout
        self.theme = theme or Theme()
        self.width = width
        self._buffer = []

    def print(self, *objects: Any, sep=" ", end="\n", style=None, justify=None):
        renderables = []
        for obj in objects:
            if isinstance(obj, str):
                renderables.append(Text.from_markup(obj, style=style or ""))
            else:
                renderables.append(obj)
        
        for i, renderable in enumerate(renderables):
            if i > 0:
                self._write(sep)
            self._render(renderable)
        
        self._write(end)

    def _render(self, renderable):
        if hasattr(renderable, "__rich_console__"):
            for segment in renderable.__rich_console__(self, None):
                self._write(str(segment))
        elif isinstance(renderable, Text):
            for segment in renderable.__rich_console__(self, None):
                self._write(str(segment))
        else:
            self._write(str(renderable))

    def _write(self, text: str):
        self.file.write(text)
        self.file.flush()

    def rule(self, title: str = "", characters: str = "─"):
        rule_width = self.width
        if title:
            side_width = (rule_width - len(title) - 2) // 2
            line = f"{characters * side_width} {title} {characters * side_width}"
            # Adjust for odd widths
            if len(line) < rule_width:
                line += characters
        else:
            line = characters * rule_width
        self.print(Text(line, style="bold"))

    def status(self, status: str):
        # Minimal status placeholder
        from contextlib import contextmanager
        @contextmanager
        def _status():
            self.print(f"[bold blue]Status:[/bold blue] {status}")
            yield
        return _status()