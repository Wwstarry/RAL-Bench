"""Table rendering."""

from typing import Optional, Union, List, Any, Iterable
from .console import Console
from .text import Text


class Column:
    """Represents a table column."""

    def __init__(
        self,
        header: Union[str, Text] = "",
        *,
        footer: Union[str, Text] = "",
        header_style: Optional[str] = None,
        footer_style: Optional[str] = None,
        style: Optional[str] = None,
        justify: str = "left",
        vertical: str = "top",
        overflow: str = "ellipsis",
        width: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        ratio: Optional[int] = None,
        no_wrap: bool = False,
    ) -> None:
        self.header = header if isinstance(header, Text) else Text(str(header))
        self.footer = footer if isinstance(footer, Text) else Text(str(footer))
        self.header_style = header_style
        self.footer_style = footer_style
        self.style = style
        self.justify = justify
        self.vertical = vertical
        self.overflow = overflow
        self.width = width
        self.min_width = min_width
        self.max_width = max_width
        self.ratio = ratio
        self.no_wrap = no_wrap
        self._cells: List[Any] = []


class Row:
    """Represents a table row."""

    def __init__(self, *cells: Any, style: Optional[str] = None, end_section: bool = False) -> None:
        self.cells = list(cells)
        self.style = style
        self.end_section = end_section


class Table:
    """A table with rows and columns."""

    def __init__(
        self,
        *headers: Union[Column, str],
        title: Optional[Union[str, Text]] = None,
        caption: Optional[Union[str, Text]] = None,
        width: Optional[int] = None,
        min_width: Optional[int] = None,
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
        style: Optional[str] = None,
        row_styles: Optional[Iterable[str]] = None,
        header_style: Optional[str] = None,
        footer_style: Optional[str] = None,
        border_style: Optional[str] = None,
        title_style: Optional[str] = None,
        caption_style: Optional[str] = None,
        title_justify: str = "center",
        caption_justify: str = "center",
        highlight: bool = False,
    ) -> None:
        self.title = title
        self.caption = caption
        self.width = width
        self.min_width = min_width
        self.box = box
        self.safe_box = safe_box
        self.padding = padding if isinstance(padding, tuple) else (0, padding)
        self.collapse_padding = collapse_padding
        self.pad_edge = pad_edge
        self.expand = expand
        self.show_header = show_header
        self.show_footer = show_footer
        self.show_edge = show_edge
        self.show_lines = show_lines
        self.leading = leading
        self.style = style
        self.row_styles = list(row_styles) if row_styles else []
        self.header_style = header_style
        self.footer_style = footer_style
        self.border_style = border_style
        self.title_style = title_style
        self.caption_style = caption_style
        self.title_justify = title_justify
        self.caption_justify = caption_justify
        self.highlight = highlight

        self.columns: List[Column] = []
        self.rows: List[Row] = []

        # Add initial columns from headers
        for header in headers:
            if isinstance(header, Column):
                self.columns.append(header)
            else:
                self.add_column(str(header))

    def add_column(
        self,
        header: Union[str, Text] = "",
        *,
        footer: Union[str, Text] = "",
        header_style: Optional[str] = None,
        footer_style: Optional[str] = None,
        style: Optional[str] = None,
        justify: str = "left",
        vertical: str = "top",
        overflow: str = "ellipsis",
        width: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        ratio: Optional[int] = None,
        no_wrap: bool = False,
    ) -> None:
        """Add a column to the table."""
        column = Column(
            header=header,
            footer=footer,
            header_style=header_style,
            footer_style=footer_style,
            style=style,
            justify=justify,
            vertical=vertical,
            overflow=overflow,
            width=width,
            min_width=min_width,
            max_width=max_width,
            ratio=ratio,
            no_wrap=no_wrap,
        )
        self.columns.append(column)

    def add_row(self, *cells: Any, style: Optional[str] = None, end_section: bool = False) -> None:
        """Add a row to the table."""
        row = Row(*cells, style=style, end_section=end_section)
        self.rows.append(row)

    def __rich_console__(self, console: Console, options: Any) -> None:
        """Render the table to the console."""
        output = self._render(console)
        console.file.write(output)

    def _render(self, console: Console) -> str:
        """Render the table to a string."""
        if not self.columns:
            return ""

        # Calculate column widths
        col_widths = self._calculate_column_widths(console)
        
        lines = []
        
        # Add title if present
        if self.title:
            title_text = str(self.title)
            lines.append(self._center_text(title_text, sum(col_widths) + len(col_widths) * 3 + 1))
        
        # Top border
        if self.show_edge:
            lines.append(self._render_border_line(col_widths, "top"))
        
        # Header
        if self.show_header:
            header_line = self._render_row(
                [col.header.plain if isinstance(col.header, Text) else str(col.header) for col in self.columns],
                col_widths
            )
            lines.append(header_line)
            
            # Header separator
            if self.rows:
                lines.append(self._render_border_line(col_widths, "mid"))
        
        # Rows
        for i, row in enumerate(self.rows):
            row_line = self._render_row(
                [self._cell_to_str(cell) for cell in row.cells],
                col_widths
            )
            lines.append(row_line)
            
            # Row separator
            if self.show_lines and i < len(self.rows) - 1:
                lines.append(self._render_border_line(col_widths, "mid"))
        
        # Bottom border
        if self.show_edge:
            lines.append(self._render_border_line(col_widths, "bottom"))
        
        # Add caption if present
        if self.caption:
            caption_text = str(self.caption)
            lines.append(self._center_text(caption_text, sum(col_widths) + len(col_widths) * 3 + 1))
        
        return "\n".join(lines) + "\n"

    def _cell_to_str(self, cell: Any) -> str:
        """Convert a cell value to string."""
        if isinstance(cell, Text):
            return cell.plain
        return str(cell)

    def _calculate_column_widths(self, console: Console) -> List[int]:
        """Calculate the width of each column."""
        col_widths = []
        
        for i, col in enumerate(self.columns):
            if col.width is not None:
                col_widths.append(col.width)
            else:
                # Calculate based on content
                max_width = len(col.header.plain if isinstance(col.header, Text) else str(col.header))
                
                for row in self.rows:
                    if i < len(row.cells):
                        cell_text = self._cell_to_str(row.cells[i])
                        max_width = max(max_width, len(cell_text))
                
                if col.min_width:
                    max_width = max(max_width, col.min_width)
                if col.max_width:
                    max_width = min(max_width, col.max_width)
                
                col_widths.append(max_width)
        
        return col_widths

    def _render_row(self, cells: List[str], col_widths: List[int]) -> str:
        """Render a single row."""
        parts = []
        
        if self.show_edge:
            parts.append("│")
        
        for i, (cell, width) in enumerate(zip(cells, col_widths)):
            # Apply padding
            pad_left, pad_right = self.padding
            
            # Justify cell content
            justify = self.columns[i].justify if i < len(self.columns) else "left"
            
            if justify == "right":
                cell_content = cell.rjust(width)
            elif justify == "center":
                cell_content = cell.center(width)
            else:  # left
                cell_content = cell.ljust(width)
            
            parts.append(" " * pad_left + cell_content + " " * pad_right)
            
            if i < len(cells) - 1 or self.show_edge:
                parts.append("│")
        
        return "".join(parts)

    def _render_border_line(self, col_widths: List[int], position: str) -> str:
        """Render a border line."""
        if position == "top":
            left, mid, right, horiz = "┌", "┬", "┐", "─"
        elif position == "bottom":
            left, mid, right, horiz = "└", "┴", "┘", "─"
        else:  # mid
            left, mid, right, horiz = "├", "┼", "┤", "─"
        
        parts = []
        
        if self.show_edge:
            parts.append(left)
        
        pad_left, pad_right = self.padding
        
        for i, width in enumerate(col_widths):
            parts.append(horiz * (width + pad_left + pad_right))
            
            if i < len(col_widths) - 1:
                parts.append(mid)
            elif self.show_edge:
                parts.append(right)
        
        return "".join(parts)

    def _center_text(self, text: str, width: int) -> str:
        """Center text within a given width."""
        padding = (width - len(text)) // 2
        return " " * padding + text