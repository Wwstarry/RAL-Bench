from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence, Tuple

from ._ansi import strip_ansi
from ._wrap import wrap_cell
from .console import Console, ConsoleOptions
from .text import Text


@dataclass
class Column:
    header: str = ""
    footer: str = ""
    justify: str = "left"  # left|center|right
    vertical: str = "top"
    style: Optional[str] = None
    header_style: Optional[str] = None
    footer_style: Optional[str] = None
    no_wrap: bool = False
    width: Optional[int] = None
    ratio: Optional[int] = None
    overflow: str = "fold"
    _cells: List[str] = field(default_factory=list, init=False, repr=False)


@dataclass
class Row:
    style: Optional[str] = None
    end_section: bool = False


class Table:
    def __init__(
        self,
        *headers: str,
        title: Optional[str] = None,
        caption: Optional[str] = None,
        width: Optional[int] = None,
        box: str = "SQUARE",
        show_header: bool = True,
        show_footer: bool = False,
        show_edge: bool = True,
        show_lines: bool = False,
        pad_edge: bool = True,
        padding: Tuple[int, int] = (0, 1),  # (top/bottom unused, left/right)
        collapse_padding: bool = False,
        expand: bool = False,
        header_style: str = "bold",
        border_style: Optional[str] = None,
        row_styles: Optional[Sequence[str]] = None,
    ) -> None:
        self.title = title
        self.caption = caption
        self.width = width
        self.show_header = show_header
        self.show_footer = show_footer
        self.show_edge = show_edge
        self.show_lines = show_lines
        self.pad_edge = pad_edge
        self.padding = padding
        self.collapse_padding = collapse_padding
        self.expand = expand
        self.header_style = header_style
        self.border_style = border_style
        self.row_styles = list(row_styles) if row_styles else []
        self.columns: List[Column] = []
        self.rows: List[Row] = []
        self._row_cells: List[List[str]] = []

        if headers:
            for h in headers:
                self.add_column(str(h))

    def add_column(
        self,
        header: str = "",
        *,
        footer: str = "",
        justify: str = "left",
        style: Optional[str] = None,
        no_wrap: bool = False,
        width: Optional[int] = None,
        ratio: Optional[int] = None,
        overflow: str = "fold",
        header_style: Optional[str] = None,
        footer_style: Optional[str] = None,
    ) -> Column:
        col = Column(
            header=str(header),
            footer=str(footer),
            justify=justify,
            style=style,
            no_wrap=no_wrap,
            width=width,
            ratio=ratio,
            overflow=overflow,
            header_style=header_style,
            footer_style=footer_style,
        )
        self.columns.append(col)
        return col

    def add_row(self, *renderables: Any, style: Optional[str] = None, end_section: bool = False) -> None:
        cells = ["" if r is None else str(r) for r in renderables]
        # pad to columns
        while len(cells) < len(self.columns):
            cells.append("")
        self._row_cells.append(cells[: len(self.columns)])
        self.rows.append(Row(style=style, end_section=end_section))
        for i, cell in enumerate(cells[: len(self.columns)]):
            self.columns[i]._cells.append(cell)

    def _measure_columns(self, console_width: int) -> List[int]:
        # base content widths (visible length)
        widths: List[int] = []
        for col in self.columns:
            candidates = [strip_ansi(col.header)] if self.show_header else []
            candidates += [strip_ansi(c) for c in col._cells]
            if self.show_footer and col.footer:
                candidates.append(strip_ansi(col.footer))
            w = max((len(s) for s in candidates), default=0)
            if col.width is not None:
                w = col.width
            widths.append(w)

        # account for padding inside cells: left/right
        pad_lr = self.padding[1] * 2
        widths = [w + pad_lr for w in widths]

        # fit to table width if specified
        if self.width is not None:
            target = self.width
        else:
            target = console_width

        # borders width
        if self.show_edge:
            border_extra = len(self.columns) + 1
        else:
            border_extra = max(0, len(self.columns) - 1)
        available = max(1, target - border_extra)

        total = sum(widths)
        if total <= available:
            return widths

        # shrink columns proportionally, but keep at least 1
        over = total - available
        while over > 0:
            # pick widest column >1
            idx = max(range(len(widths)), key=lambda i: widths[i])
            if widths[idx] <= 1:
                break
            widths[idx] -= 1
            over -= 1
        return widths

    def _align(self, s: str, width: int, justify: str) -> str:
        vis = len(strip_ansi(s))
        if vis >= width:
            return s
        spaces = width - vis
        if justify == "right":
            return " " * spaces + s
        if justify == "center":
            left = spaces // 2
            right = spaces - left
            return " " * left + s + " " * right
        return s + " " * spaces

    def _render_border(self, left: str, mid: str, right: str, widths: List[int]) -> str:
        if not self.show_edge:
            return ""
        parts = [left]
        for i, w in enumerate(widths):
            parts.append("─" * w)
            parts.append(right if i == len(widths) - 1 else mid)
        return "".join(parts)

    def _render_row_line(self, cells: List[str], widths: List[int]) -> List[str]:
        # wrap each cell to width minus padding
        pad = self.padding[1]
        inner_widths = [max(1, w - pad * 2) for w in widths]
        wrapped_cells: List[List[str]] = []
        for i, cell in enumerate(cells):
            col = self.columns[i]
            lines = wrap_cell(cell, inner_widths[i], no_wrap=col.no_wrap)
            wrapped_cells.append(lines)

        height = max((len(lines) for lines in wrapped_cells), default=1)
        out_lines: List[str] = []
        for r in range(height):
            line_parts: List[str] = []
            if self.show_edge:
                line_parts.append("│")
            for i in range(len(widths)):
                col = self.columns[i]
                content = wrapped_cells[i][r] if r < len(wrapped_cells[i]) else ""
                content = self._align(content, inner_widths[i], col.justify)
                cell_text = (" " * pad) + content + (" " * pad)
                line_parts.append(cell_text)
                if self.show_edge:
                    line_parts.append("│")
                else:
                    if i != len(widths) - 1:
                        line_parts.append("│")
            out_lines.append("".join(line_parts))
        return out_lines

    def __rich_console__(self, console: Console, options: ConsoleOptions):
        yield Text(self.__str__())

    def __str__(self) -> str:
        console_width = 80
        widths = self._measure_columns(console_width)

        top = self._render_border("┌", "┬", "┐", widths)
        mid = self._render_border("├", "┼", "┤", widths)
        bottom = self._render_border("└", "┴", "┘", widths)

        lines: List[str] = []
        if self.show_edge:
            lines.append(top)

        if self.show_header:
            header_cells = [c.header for c in self.columns]
            lines.extend(self._render_row_line(header_cells, widths))
            lines.append(mid)

        for row_index, cells in enumerate(self._row_cells):
            lines.extend(self._render_row_line(cells, widths))
            if self.show_lines and row_index != len(self._row_cells) - 1:
                lines.append(mid)
            elif row_index < len(self.rows) and self.rows[row_index].end_section:
                lines.append(mid)

        if self.show_edge:
            lines.append(bottom)

        return "\n".join(lines)