"""
A very small subset of *rich.table*.

The implementation focuses on **deterministic** string output for unit-tests
and does **not** attempt to replicate all features of the real Rich project.
"""

from __future__ import annotations

import itertools
from typing import List


# --------------------------------------------------------------------------- #
# helper                                                                      #
# --------------------------------------------------------------------------- #


def _align(text: str, width: int, justify: str) -> str:
    """
    Simple alignment helper respecting *left*, *center*, *right*.
    """
    if justify == "right":
        return text.rjust(width)
    if justify == "center":
        return text.center(width)
    # default / left
    return text.ljust(width)


# --------------------------------------------------------------------------- #
# Column                                                                      #
# --------------------------------------------------------------------------- #


class Column:
    """
    Sub-set of :class:`rich.table.Column`.

    Parameters
    ----------
    header:
        Header text for the column.
    justify:
        left / center / right alignment.
    """

    def __init__(
        self,
        header: str,
        *,
        justify: str = "left",
        style: str | None = None,
        no_wrap: bool = False,
    ) -> None:
        self.header: str = header
        self.justify: str = justify
        self.style: str | None = style
        self.no_wrap: bool = no_wrap

    # expose the attribute as Rich does
    header_style = property(lambda self: self.style or "")


# --------------------------------------------------------------------------- #
# Row                                                                         #
# --------------------------------------------------------------------------- #


class Row:
    """Very small representation of a table row."""

    def __init__(self, cells: List[str]) -> None:
        self.cells = cells

    # the real Rich uses __rich_console__ – for our needs str() is good enough
    def __str__(self) -> str:  # pragma: no cover (never called directly)
        return f"Row({self.cells})"


# --------------------------------------------------------------------------- #
# Table                                                                       #
# --------------------------------------------------------------------------- #


class Table:
    """
    Simple ASCII table implementation.

    Not all parameters of the real *rich.table.Table* are honoured – only the
    ones that are observed by the tests.
    """

    def __init__(
        self,
        *,
        title: str | None = None,
        show_header: bool = True,
        show_lines: bool = False,
    ) -> None:
        self.title: str | None = title
        self.show_header: bool = show_header
        self.show_lines: bool = show_lines

        self.columns: list[Column] = []
        self._rows: list[Row] = []

    # --------------------------------------------------------------------- #
    # API replicates real Rich                                              #
    # --------------------------------------------------------------------- #

    def add_column(
        self,
        header: str,
        *,
        justify: str = "left",
        style: str | None = None,
        no_wrap: bool = False,
    ) -> None:
        self.columns.append(
            Column(header, justify=justify, style=style, no_wrap=no_wrap)
        )

    def add_row(self, *cells: str) -> None:
        if not self.columns:
            raise ValueError("Cannot add a row before adding columns.")
        if len(cells) != len(self.columns):
            raise ValueError("Row has different number of cells than table columns.")
        self._rows.append(Row(list(cells)))

    # --------------------------------------------------------------------- #
    # Rendering                                                             #
    # --------------------------------------------------------------------- #

    def _compute_widths(self) -> list[int]:
        """
        Determine the width of every column from header *and* cell content.
        """
        widths: list[int] = [len(col.header) for col in self.columns]
        for row in self._rows:
            for idx, cell in enumerate(row.cells):
                widths[idx] = max(widths[idx], len(str(cell)))
        return widths

    def __rich__(self) -> str:  # allow Console to call ``__rich__``
        return str(self)

    def __str__(self) -> str:
        widths = self._compute_widths()
        total_inner = sum(widths) + 3 * (len(widths) - 1)
        lines: list[str] = []

        # Title line (simple centred line placed *above* the table)
        if self.title:
            lines.append(self.title.center(total_inner + 2))  # +2 for borders

        # Borders helpers -------------------------------------------------- #
        def border_line(left: str, mid: str, right: str, fill: str) -> str:
            parts = [fill * (w + 2) for w in widths]
            return left + mid.join(parts) + right

        top = border_line("┏", "┳", "┓", "━")
        header_sep = border_line("┡", "╇", "┩", "━")
        row_sep = border_line("├", "┼", "┤", "─")
        bottom = border_line("└", "┴", "┘", "─")

        lines.append(top)

        # Header ----------------------------------------------------------- #
        if self.show_header:
            rendered_header = []
            for col, width in zip(self.columns, widths):
                rendered_header.append(_align(col.header, width, col.justify))
            lines.append(
                "┃ "
                + " ┃ ".join(rendered_header)
                + " ┃"
            )
            lines.append(header_sep)

        # Rows ------------------------------------------------------------- #
        for ridx, row in enumerate(self._rows):
            rendered_cells = []
            for cell, col, width in zip(row.cells, self.columns, widths):
                rendered_cells.append(_align(str(cell), width, col.justify))
            lines.append("│ " + " │ ".join(rendered_cells) + " │")

            # optional inner line
            if self.show_lines and ridx != len(self._rows) - 1:
                lines.append(row_sep)

        # bottom border
        lines.append(bottom)
        return "\n".join(lines)


# expose classes via rich.table
__all__ = ["Table", "Column", "Row"]