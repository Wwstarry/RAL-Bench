"""Table rendering for the console."""

from typing import Optional, List, Union, Any, Iterable
from enum import Enum


class Column:
    """Represents a column in a table."""

    def __init__(
        self,
        header: str = "",
        footer: str = "",
        style: Optional[str] = None,
        justify: str = "left",
        width: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        no_wrap: bool = False,
        overflow: str = "fold",
        ratio: Optional[int] = None,
    ):
        """Initialize a Column."""
        self.header = header
        self.footer = footer
        self.style = style
        self.justify = justify
        self.width = width
        self.min_width = min_width
        self.max_width = max_width
        self.no_wrap = no_wrap
        self.overflow = overflow
        self.ratio = ratio


class Row:
    """Represents a row in a table."""

    def __init__(self, *cells: Any, style: Optional[str] = None, end_section: bool = False):
        """Initialize a Row."""
        self.cells = list(cells)
        self.style = style
        self.end_section = end_section


class Table:
    """A table for displaying data in rows and columns."""

    def __init__(
        self,
        *columns: Union[str, Column],
        title: Optional[str] = None,
        caption: Optional[str] = None,
        width: Optional[int] = None,
        box: Optional[Any] = None,
        safe_box: Optional[bool] = None,
        padding: Union[int, tuple] = (0, 1),
        collapse_padding: bool = False,
        pad_edge: bool = True,
        expand: bool = False,
        show_header: bool = True,
        show_footer: bool = False,
        show_edge: bool = True,
        show_lines: bool = False,
        leading: int = 0,
        trailing: int = 0,
        style: Optional[str] = None,
        row_styles: Optional[List[str]] = None,
        header_style: Optional[str] = None,
        footer_style: Optional[str] = None,
        border_style: Optional[str] = None,
        title_style: Optional[str] = None,
        caption_style: Optional[str] = None,
    ):
        """Initialize a Table."""
        self.title = title
        self.caption = caption
        self.width = width
        self.box = box
        self.safe_box = safe_box
        self.padding = padding if isinstance(padding, tuple) else (padding, padding)
        self.collapse_padding = collapse_padding
        self.pad_edge = pad_edge
        self.expand = expand
        self.show_header = show_header
        self.show_footer = show_footer
        self.show_edge = show_edge
        self.show_lines = show_lines
        self.leading = leading
        self.trailing = trailing
        self.style = style
        self.row_styles = row_styles or []
        self.header_style = header_style
        self.footer_style = footer_style
        self.border_style = border_style
        self.title_style = title_style
        self.caption_style = caption_style

        # Initialize columns
        self.columns: List[Column] = []
        for col in columns:
            if isinstance(col, str):
                self.columns.append(Column(header=col))
            else:
                self.columns.append(col)

        # Initialize rows
        self.rows: List[Row] = []

    def add_column(
        self,
        header: str = "",
        footer: str = "",
        style: Optional[str] = None,
        justify: str = "left",
        width: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        no_wrap: bool = False,
        overflow: str = "fold",
        ratio: Optional[int] = None,
    ) -> None:
        """Add a column to the table."""
        column = Column(
            header=header,
            footer=footer,
            style=style,
            justify=justify,
            width=width,
            min_width=min_width,
            max_width=max_width,
            no_wrap=no_wrap,
            overflow=overflow,
            ratio=ratio,
        )
        self.columns.append(column)

    def add_row(self, *cells: Any, style: Optional[str] = None, end_section: bool = False) -> None:
        """Add a row to the table."""
        row = Row(*cells, style=style, end_section=end_section)
        self.rows.append(row)

    def __rich_console__(self, console: Any, options: Any) -> str:
        """Render the table for console output."""
        return self._render_table(console)

    def _render_table(self, console: Any) -> str:
        """Render the table as a string."""
        if not self.columns:
            return ""

        # Calculate column widths
        col_widths = self._calculate_column_widths(console)

        lines = []

        # Add title if present
        if self.title:
            lines.append(self.title)

        # Add header
        if self.show_header:
            header_line = self._render_row(
                [col.header for col in self.columns],
                col_widths,
                is_header=True,
            )
            lines.append(header_line)

        # Add rows
        for row in self.rows:
            row_line = self._render_row(row.cells, col_widths)
            lines.append(row_line)

        # Add footer
        if self.show_footer:
            footer_line = self._render_row(
                [col.footer for col in self.columns],
                col_widths,
                is_footer=True,
            )
            lines.append(footer_line)

        # Add caption if present
        if self.caption:
            lines.append(self.caption)

        return "\n".join(lines)

    def _calculate_column_widths(self, console: Any) -> List[int]:
        """Calculate the width of each column."""
        widths = []

        for col_idx, col in enumerate(self.columns):
            # Start with header width
            max_width = len(str(col.header))

            # Check footer width
            if self.show_footer:
                max_width = max(max_width, len(str(col.footer)))

            # Check all row widths
            for row in self.rows:
                if col_idx < len(row.cells):
                    cell_width = len(str(row.cells[col_idx]))
                    max_width = max(max_width, cell_width)

            # Apply padding
            padding_left, padding_right = self.padding
            max_width += padding_left + padding_right

            # Apply min/max width constraints
            if col.min_width is not None:
                max_width = max(max_width, col.min_width)
            if col.max_width is not None:
                max_width = min(max_width, col.max_width)
            if col.width is not None:
                max_width = col.width

            widths.append(max_width)

        return widths

    def _render_row(
        self,
        cells: List[Any],
        col_widths: List[int],
        is_header: bool = False,
        is_footer: bool = False,
    ) -> str:
        """Render a single row."""
        padding_left, padding_right = self.padding

        rendered_cells = []
        for col_idx, cell in enumerate(cells):
            if col_idx >= len(col_widths):
                break

            cell_str = str(cell)
            col_width = col_widths[col_idx]
            col = self.columns[col_idx]

            # Apply padding
            cell_width = col_width - padding_left - padding_right

            # Justify the cell content
            if col.justify == "center":
                cell_str = cell_str.center(cell_width)
            elif col.justify == "right":
                cell_str = cell_str.rjust(cell_width)
            else:  # left
                cell_str = cell_str.ljust(cell_width)

            # Add padding
            cell_str = " " * padding_left + cell_str + " " * padding_right
            rendered_cells.append(cell_str)

        # Join cells with separators
        return " ".join(rendered_cells)