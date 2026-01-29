from typing import Any, List, Optional, Union
from rich.text import Text

class Column:
    def __init__(
        self,
        header: Union[str, Text] = "",
        style: Optional[str] = None,
        width: Optional[int] = None,
    ):
        self.header = str(header) if isinstance(header, str) else header
        self.style = style
        self._width = width
        
    @property
    def width(self) -> int:
        if self._width:
            return self._width
        header_width = len(str(self.header)) if self.header else 0
        return max(header_width, 1)

class Row:
    def __init__(self, *cells: Any, style: Optional[str] = None):
        self.cells = [str(cell) for cell in cells]
        self.style = style

class Table:
    def __init__(
        self,
        *,
        title: Optional[str] = None,
        title_style: Optional[str] = None,
        show_header: bool = True,
        show_footer: bool = False,
        show_edge: bool = True,
        show_lines: bool = False,
        padding: int = 1,
    ):
        self.title = title
        self.title_style = title_style
        self.show_header = show_header
        self.show_footer = show_footer
        self.show_edge = show_edge
        self.show_lines = show_lines
        self.padding = padding
        
        self.columns: List[Column] = []
        self.rows: List[Row] = []
        
    def add_column(
        self,
        header: Union[str, Text] = "",
        style: Optional[str] = None,
        width: Optional[int] = None,
    ) -> None:
        """Add a column to the table."""
        column = Column(header=header, style=style, width=width)
        self.columns.append(column)
        
    def add_row(self, *cells: Any, style: Optional[str] = None) -> None:
        """Add a row to the table."""
        row = Row(*cells, style=style)
        self.rows.append(row)
        
    def __str__(self) -> str:
        """Render the table as a string."""
        if not self.columns:
            return ""
            
        # Calculate column widths
        col_widths = []
        for i, column in enumerate(self.columns):
            max_width = column.width
            for row in self.rows:
                if i < len(row.cells):
                    cell_width = len(row.cells[i])
                    max_width = max(max_width, cell_width)
            col_widths.append(max_width)
            
        # Build the table
        lines = []
        
        # Title
        if self.title:
            title_line = f" {self.title} "
            if self.title_style:
                # Simplified styling
                title_line = f"[{self.title_style}]{title_line}[/]"
            lines.append(title_line.center(sum(col_widths) + len(col_widths) * 3 - 1))
            lines.append("")
        
        # Header
        if self.show_header and self.columns:
            header_cells = []
            for i, column in enumerate(self.columns):
                header_text = str(column.header) if column.header else ""
                padded_header = header_text.center(col_widths[i] + self.padding * 2)
                header_cells.append(padded_header)
                
            header_line = "│".join(header_cells)
            if self.show_edge:
                header_line = f"│{header_line}│"
            lines.append(header_line)
            
            # Header separator
            sep_parts = []
            for width in col_widths:
                sep_parts.append("─" * (width + self.padding * 2))
            sep_line = "┼".join(sep_parts)
            if self.show_edge:
                sep_line = f"├{sep_line}┤"
            lines.append(sep_line)
        
        # Rows
        for row in self.rows:
            row_cells = []
            for i, cell in enumerate(row.cells):
                if i < len(col_widths):
                    padded_cell = cell.ljust(col_widths[i] + self.padding * 2)
                    row_cells.append(padded_cell)
                    
            row_line = "│".join(row_cells)
            if self.show_edge:
                row_line = f"│{row_line}│"
            lines.append(row_line)
            
        # Footer
        if self.show_footer and self.rows:
            footer_sep_parts = []
            for width in col_widths:
                footer_sep_parts.append("─" * (width + self.padding * 2))
            footer_sep_line = "┼".join(footer_sep_parts)
            if self.show_edge:
                footer_sep_line = f"├{footer_sep_line}┤"
            lines.append(footer_sep_line)
            
        return "\n".join(lines)