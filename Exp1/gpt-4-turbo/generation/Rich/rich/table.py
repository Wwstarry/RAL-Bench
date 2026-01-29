from typing import List, Optional, Any, Dict, Union
from .text import Text

class Column:
    def __init__(self, header: str, justify: str = "left", width: Optional[int] = None, style: Optional[str] = None, no_wrap: bool = False):
        self.header = header
        self.justify = justify
        self.width = width
        self.style = style
        self.no_wrap = no_wrap

class Row:
    def __init__(self, cells: List[Any], style: Optional[str] = None):
        self.cells = cells
        self.style = style

class Table:
    def __init__(self, show_header: bool = True, show_footer: bool = False, title: Optional[str] = None, caption: Optional[str] = None, box: bool = True, padding: int = 1, width: Optional[int] = None):
        self.columns: List[Column] = []
        self.rows: List[Row] = []
        self.show_header = show_header
        self.show_footer = show_footer
        self.title = title
        self.caption = caption
        self.box = box
        self.padding = padding
        self.width = width

    def add_column(self, header: str, justify: str = "left", width: Optional[int] = None, style: Optional[str] = None, no_wrap: bool = False):
        self.columns.append(Column(header, justify, width, style, no_wrap))

    def add_row(self, *cells: Any, style: Optional[str] = None):
        self.rows.append(Row(list(cells), style))

    def __rich__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        # Calculate column widths
        col_widths = []
        for idx, col in enumerate(self.columns):
            max_content = len(str(col.header))
            for row in self.rows:
                cell = row.cells[idx] if idx < len(row.cells) else ""
                cell_str = str(cell)
                max_content = max(max_content, len(cell_str))
            col_widths.append(col.width or max_content + self.padding * 2)

        # Table border chars
        if self.box:
            top_left, top_mid, top_right = "┌", "┬", "┐"
            mid_left, mid_mid, mid_right = "├", "┼", "┤"
            bot_left, bot_mid, bot_right = "└", "┴", "┘"
            hor, ver = "─", "│"
        else:
            top_left = top_mid = top_right = ""
            mid_left = mid_mid = mid_right = ""
            bot_left = bot_mid = bot_right = ""
            hor = ver = " "

        # Top border
        out = ""
        if self.box:
            out += top_left
            for i, w in enumerate(col_widths):
                out += hor * w
                out += top_mid if i < len(col_widths) - 1 else top_right
            out += "\n"

        # Title
        if self.title:
            out += f"{ver}{self.title.center(sum(col_widths))}{ver}\n"

        # Header
        if self.show_header:
            out += ver
            for i, col in enumerate(self.columns):
                txt = str(col.header)
                txt = txt.center(col_widths[i]) if col.justify == "center" else txt.ljust(col_widths[i]) if col.justify == "left" else txt.rjust(col_widths[i])
                out += txt
                out += ver
            out += "\n"
            # Header separator
            if self.box:
                out += mid_left
                for i, w in enumerate(col_widths):
                    out += hor * w
                    out += mid_mid if i < len(col_widths) - 1 else mid_right
                out += "\n"

        # Rows
        for row in self.rows:
            out += ver
            for i, col in enumerate(self.columns):
                cell = row.cells[i] if i < len(row.cells) else ""
                cell_str = str(cell)
                cell_str = cell_str.center(col_widths[i]) if col.justify == "center" else cell_str.ljust(col_widths[i]) if col.justify == "left" else cell_str.rjust(col_widths[i])
                out += cell_str
                out += ver
            out += "\n"

        # Bottom border
        if self.box:
            out += bot_left
            for i, w in enumerate(col_widths):
                out += hor * w
                out += bot_mid if i < len(col_widths) - 1 else bot_right
            out += "\n"

        # Caption
        if self.caption:
            out += f"{self.caption}\n"

        return out