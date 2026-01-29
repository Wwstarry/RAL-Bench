from __future__ import annotations

import math
from typing import Any, Iterable, List, Optional, Sequence, Tuple


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


class Column:
    def __init__(
        self,
        header: str,
        justify: Optional[str] = None,
        no_wrap: bool = False,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        padding: Tuple[int, int] = (1, 1),
    ) -> None:
        self.header = header
        self.justify = justify
        self.no_wrap = no_wrap
        self.min_width = min_width
        self.max_width = max_width
        self.padding = padding  # left, right

    def measure(self, cells: Iterable[str]) -> int:
        content_width = max([len(self.header)] + [len(c) for c in cells] + [0])
        if self.min_width is not None:
            content_width = max(content_width, self.min_width)
        if self.max_width is not None:
            content_width = min(content_width, self.max_width)
        return content_width


class Row:
    def __init__(self, cells: Sequence[Any]) -> None:
        self.cells = list(cells)

    def __iter__(self):
        return iter(self.cells)


class Table:
    def __init__(
        self,
        show_header: bool = True,
        header_style: Optional[str] = None,
        expand: bool = False,
        padding: Tuple[int, int] = (0, 0),
        title: Optional[str] = None,
    ) -> None:
        self.columns: List[Column] = []
        self.rows: List[Row] = []
        self.show_header = show_header
        self.header_style = header_style
        self.expand = expand
        self.padding = padding
        self.title = title

    def add_column(
        self,
        header: str,
        justify: Optional[str] = None,
        no_wrap: bool = False,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        padding: Optional[Tuple[int, int]] = None,
    ) -> None:
        col = Column(
            header=header,
            justify=justify,
            no_wrap=no_wrap,
            min_width=min_width,
            max_width=max_width,
            padding=padding if padding is not None else (1, 1),
        )
        self.columns.append(col)

    def add_row(self, *cells: Any) -> None:
        if not self.columns:
            # Implicit columns if not defined
            for _ in range(len(cells)):
                self.add_column("")
        # pad or trim cells to columns count
        cell_list = list(cells[: len(self.columns)])
        if len(cell_list) < len(self.columns):
            cell_list.extend([""] * (len(self.columns) - len(cell_list)))
        self.rows.append(Row(cell_list))

    def _justify(self, text: str, width: int, justify: Optional[str]) -> str:
        if justify == "right":
            return text.rjust(width)
        elif justify == "center" or justify == "centre":
            return text.center(width)
        else:
            return text.ljust(width)

    def _compute_widths(self, width: int) -> List[int]:
        # measure intrinsic content widths
        col_cells = list(zip(*[r.cells for r in self.rows], strict=False)) if self.rows else []
        widths: List[int] = []
        for i, col in enumerate(self.columns):
            cells = []
            if col_cells:
                try:
                    for cell in col_cells[i]:
                        cells.append(_stringify(cell).split("\n")[0])
                except IndexError:
                    pass
            content = col.measure(cells)
            content += sum(col.padding)
            widths.append(content)

        border_space = 1 + len(self.columns) + 1  # vertical lines count approximated spaces
        # Our borders take 2 side + (n-1) separators, each 1 char wide:
        borders = 2 + max(0, len(self.columns) - 1)
        total_width = sum(widths) + borders

        if width > 0 and total_width > width:
            # Reduce per-column widths by wrapping content; ensure minimum of 3 + padding
            available = max(width - borders, 1)
            base = max(1, available // max(1, len(self.columns)))
            # distribute extra remainder
            widths = [max(3 + sum(self.columns[i].padding), min(w, base)) for i, w in enumerate(widths)]
            # If still too large, adjust
            while sum(widths) > available:
                # shrink the largest column
                idx = max(range(len(widths)), key=lambda j: widths[j])
                if widths[idx] <= (3 + sum(self.columns[idx].padding)):
                    break
                widths[idx] -= 1

        # remove padding from returned widths as content width
        content_widths = [max(0, w - sum(self.columns[i].padding)) for i, w in enumerate(widths)]
        return content_widths

    def _split_cell(self, text: str, width: int, no_wrap: bool) -> List[str]:
        lines = []
        for part in str(text).split("\n"):
            if no_wrap or width <= 0:
                lines.append(part)
            else:
                while len(part) > width:
                    lines.append(part[:width])
                    part = part[width:]
                lines.append(part)
        return lines

    def render(self, width: int = 80) -> str:
        if not self.columns:
            return ""
        col_widths = self._compute_widths(width)
        # borders: ┌ ┬ ┐, │, ├ ┼ ┤, └ ┴ ┘, horizontal ─
        horiz = "─"
        vert = "│"
        top_l, top_t, top_r = "┌", "┬", "┐"
        mid_l, mid_t, mid_r = "├", "┼", "┤"
        bot_l, bot_t, bot_r = "└", "┴", "┘"

        def make_border(left: str, mid: str, right: str) -> str:
            parts = []
            for i, w in enumerate(col_widths):
                # add padding width too
                pad = sum(self.columns[i].padding)
                parts.append(horiz * (w + pad))
            return left + mid.join(parts) + right

        lines: List[str] = []
        # Optional title
        if self.title:
            title = str(self.title)
            full_width = sum(col_widths) + sum(sum(c.padding) for c in self.columns) + (2 + max(0, len(self.columns) - 1))
            if len(title) > full_width:
                title = title[:full_width]
            else:
                title = title.center(full_width)
            lines.append(title)

        lines.append(make_border(top_l, top_t, top_r))

        # Header row
        if self.show_header:
            header_lines: List[List[str]] = []
            max_header_height = 1
            for i, col in enumerate(self.columns):
                header_text = _stringify(col.header)
                wrapped = self._split_cell(header_text, col_widths[i], no_wrap=True)
                header_lines.append(wrapped)
                max_header_height = max(max_header_height, len(wrapped))

            for sub in range(max_header_height):
                row_parts: List[str] = []
                for i, col in enumerate(self.columns):
                    left_pad, right_pad = col.padding
                    cell_lines = header_lines[i]
                    cell_text = cell_lines[sub] if sub < len(cell_lines) else ""
                    cell_text = self._justify(cell_text, col_widths[i], "center")
                    row_parts.append(" " * left_pad + cell_text + " " * right_pad)
                lines.append(vert + vert.join(row_parts) + vert)
            lines.append(make_border(mid_l, mid_t, mid_r))

        # Body rows
        for row in self.rows:
            cell_lines: List[List[str]] = []
            max_height = 1
            for i, col in enumerate(self.columns):
                value = row.cells[i] if i < len(row.cells) else ""
                text = _stringify(value)
                # infer justify if None and numeric
                justify = col.justify
                if justify is None and isinstance(value, (int, float)):
                    justify = "right"
                wrapped = self._split_cell(text, col_widths[i], no_wrap=col.no_wrap)
                max_height = max(max_height, len(wrapped))
                # apply justification to each wrapped line
                wrapped = [self._justify(part, col_widths[i], justify) for part in wrapped]
                cell_lines.append(wrapped)

            for sub in range(max_height):
                row_parts: List[str] = []
                for i, col in enumerate(self.columns):
                    left_pad, right_pad = col.padding
                    parts = cell_lines[i]
                    cell_text = parts[sub] if sub < len(parts) else " " * col_widths[i]
                    row_parts.append(" " * left_pad + cell_text + " " * right_pad)
                lines.append(vert + vert.join(row_parts) + vert)

        lines.append(make_border(bot_l, bot_t, bot_r))
        return "\n".join(lines)

    def __str__(self) -> str:
        # Fallback render width 80
        return self.render(80)